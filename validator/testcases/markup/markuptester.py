import re
import sys
import types
try:
    import HTMLParser as htmlparser
except ImportError:  # pragma: no cover
    import html.parser as htmlparser

import validator.testcases.scripting as scripting
import validator.unicodehelper as unicodehelper
from validator.testcases.markup import csstester
from validator.contextgenerator import ContextGenerator
from validator.constants import *
from validator.compat import FX6_DEFINITION
from validator.decorator import version_range

DEBUG = False

UNSAFE_TAGS = ("script", "object", "embed", "base", )
UNSAFE_THEME_TAGS = ("implementation", "browser", "xul:browser", "xul:script")
SELF_CLOSING_TAGS = ("area", "base", "basefont", "br", "col", "frame", "hr",
                     "img", "input", "li", "link", "meta", "p", "param", )
SAFE_IFRAME_TYPES = ("content", "content-primary", "content-targetable", )
TAG_NOT_OPENED = "Tag (%s) being closed before it is opened."

DOM_MUTATION_HANDLERS = (
        "ondomattrmodified", "ondomattributenamechanged",
        "ondomcharacterdatamodified", "ondomelementnamechanged",
        "ondomnodeinserted", "ondomnodeinsertedintodocument", "ondomnoderemoved",
        "ondomnoderemovedfromdocument", "ondomsubtreemodified", )
UNSAFE_THEME_XBL = ("constructor", "destructor", "field", "getter",
                    "implementation", "setter", )

GENERIC_IDS = ("string-bundle", "strings", )


class MarkupParser(htmlparser.HTMLParser):
    """Parse and analyze the versious components of markup files."""

    def __init__(self, err, strict=True, debug=False):
        htmlparser.HTMLParser.__init__(self)
        self.err = err
        self.is_jetpack = "is_jetpack" in err.metadata  # Cache this value.
        self.line = 0
        self.strict = strict
        self.debug = debug

        self.context = None

        self.xml_state = []
        self.xml_line_stack = []
        self.xml_buffer = []
        self.xbl = False

        self.reported = set()
        self.found_scripts = set()  # A set of script URLs in the doc.

        # Added as a patch for various Python HTMLParser issues.
        self.cdata_tag = None

    def process(self, filename, data, extension="xul"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""

        self.line = 0
        self.filename = filename
        self.extension = extension.lower()

        self.reported = set()

        self.context = ContextGenerator(data)

        lines = data.split("\n")

        buffering = False
        pline = 0
        for line in lines:
            self.line += 1

            search_line = line
            while True:
                # If a CDATA element is found, push it and its contents to the
                # buffer. Push everything previous to it to the parser.
                if "<![CDATA[" in search_line and not buffering:
                    # Find the CDATA element.
                    cdatapos = search_line.find("<![CDATA[")

                    # If the element isn't at the start of the line, pass
                    # everything before it to the parser.
                    if cdatapos:
                        self._feed_parser(search_line[:cdatapos])
                    # Collect the rest of the line to send it to the buffer.
                    search_line = search_line[cdatapos:]
                    buffering = True
                    continue

                elif "]]>" in search_line and buffering:
                    # If we find the end element on the line being scanned,
                    # buffer everything up to the end of it, and let the rest
                    # of the line pass through for further processing.
                    end_cdatapos = search_line.find("]]>") + 3
                    self._save_to_buffer(search_line[:end_cdatapos])
                    search_line = search_line[end_cdatapos:]
                    buffering = False
                break

            if buffering:
                self._save_to_buffer(search_line + "\n")
            else:
                self._feed_parser(search_line)

    def _feed_parser(self, line):
        """Feed incoming data into the underlying HTMLParser."""

        line = unicodehelper.decode(line)

        try:
            self.feed(line + "\n")
        except UnicodeDecodeError, exc_instance:
            exc_class, val, traceback = sys.exc_info()
            try:
                line = line.decode("ascii", "ignore")
                self.feed(line + "\n")
            except Exception:
                raise exc_instance, None, traceback

        except Exception as inst:
            if DEBUG:  # pragma: no cover
                print self.xml_state, inst

            if "markup" in self.reported:
                return

            if ("script" in self.xml_state or
                self.debug and "testscript" in self.xml_state):
                if "script_comments" in self.reported or not self.strict:
                    return
                self.err.notice(("testcases_markup_markuptester",
                                 "_feed",
                                 "missing_script_comments"),
                                "Missing comments in <script> tag",
                                "Markup parsing errors occurred while trying "
                                "to parse the file. This would likely be "
                                "mitigated by wrapping <script> tag contents "
                                "in HTML comment tags (<!-- -->)",
                                self.filename,
                                line=self.line,
                                context=self.context,
                                tier=2)
                self.reported.add("script_comments")
                return

            if self.strict:
                self.err.warning(("testcases_markup_markuptester",
                                  "_feed",
                                  "parse_error"),
                                 "Markup parsing error",
                                 ["There was an error parsing a markup "
                                  "file.",
                                  str(inst)],
                                 self.filename,
                                 line=self.line,
                                 context=self.context)
            self.reported.add("markup")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, True)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs, self_closing=False):

        # Normalize!
        tag = tag.lower()
        # XUL scripts are identical to normal scripts. Treat them the same.
        if tag == "xul:script":
            tag = "script"

        orig_tag = tag

        # Be extra sure it's not a self-closing tag.
        if not self_closing:
            self_closing = tag in SELF_CLOSING_TAGS

        if DEBUG:  # pragma: no cover
            print "S: ", self.xml_state, tag, self_closing

        # A fictional tag for testing purposes.
        if tag == "xbannedxtestx":
            self.err.error(
                err_id=("testcases_markup_markuptester",
                        "handle_starttag",
                        "banned_element"),
                error="Banned markup element",
                description="A banned markup element was found.",
                filename=self.filename,
                line=self.line,
                context=self.context)

        # Test for banned XBL in themes.
        if self.err.detected_type == PACKAGE_THEME:
            if tag.startswith("xbl:"):
                self.xbl = True
                tag = tag[4:]

            # Find XBL elements.
            if self.xbl:
                if tag in UNSAFE_THEME_XBL:
                    self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag",
                                "unsafe_theme_xbl_element"),
                        warning="Banned XBL element in theme.",
                        description=["Certain XBL elements are disallowed in "
                                     "themes.",
                                     "Element: <xbl:%s>" % tag],
                        filename=self.filename,
                        line=self.line,
                        context=self.context)

                elif (tag == "property" and
                      any(a[0] in (u"onset", u"onget") for a in attrs)):
                    self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag",
                                "theme_xbl_property"),
                        warning="Themes are not allowed to use XBL properties",
                        description="XBL properties cannot be used in themes.",
                        filename=self.filename,
                        line=self.line,
                        context=self.context)

        # Test for banned elements in language pack and theme markup.
        if self.err.detected_type in (PACKAGE_LANGPACK, PACKAGE_THEME):
            if (tag in UNSAFE_TAGS or
                (self.err.detected_type == PACKAGE_THEME and
                 tag in UNSAFE_THEME_TAGS)):
                self.err.warning(
                    err_id=("testcases_markup_markuptester",
                            "handle_starttag",
                            "unsafe_langpack_theme"),
                    warning="Unsafe tag for add-on type",
                    description=["A tag in your markup has been marked as "
                                 "being potentially unsafe. Consider "
                                 "alternate means of accomplishing what the "
                                 "code executed by this tag performs.",
                                 'Tag "%s" is disallowed.' % tag],
                    filename=self.filename,
                    line=self.line,
                    context=self.context)
                if DEBUG:  # pragma: no cover
                    print "Unsafe Tag ------"

            # Make sure all src/href attributes are local
            for attr in attrs:
                if attr[0].lower() in ("src", "href") and \
                   not self._is_url_local(attr[1].lower()):
                    self.err.warning(("testcases_markup_markuptester",
                                      "handle_starttag",
                                      "remote_src_href"),
                                     "src/href attributes must be local.",
                                     "Language packs require that all src and "
                                     "href attributes are relative URLs.",
                                     self.filename,
                                     line=self.line,
                                     context=self.context)

        if tag == "prefwindow":
            # Flag <prefwindow> elements without IDs.

            if not any((key == "id") for key, val in attrs):
                self.err.warning(
                        err_id=("markup", "starttag", "prefwindow_id"),
                        warning="`<prefwindow>` elements must have IDs.",
                        description="`<prefwindow>` elements without `id` "
                                    "attributes cause errors to be reported "
                                    "in the error console and prevent "
                                    "persistence of certain properties of the "
                                    "dialog.",
                        filename=self.filename,
                        line=self.line,
                        context=self.context)

        elif tag in ("iframe", "browser") and self.extension == "xul":
            # Bork if XUL iframe has no type attribute

            type_ = None
            src = None
            for attr in attrs:
                attr_name = attr[0].lower()
                if attr_name == "type":
                    type_ = attr[1].lower()
                elif attr_name == "src":
                    src = attr[1].lower()

            # We say it's true by default to catch elements that are
            # type="chrome" without an src="" attribute.
            remote_src = True
            if isinstance(src, types.StringTypes):
                remote_src = not self._is_url_local(src)

            if (type_ and
                not (type_ in SAFE_IFRAME_TYPES or
                     not remote_src)):
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "iframe_type_unsafe"),
                                 "iframe/browser missing 'type' attribute",
                                 "All iframe and browser elements must have "
                                 "either a valid `type` attribute or a `src` "
                                 "attribute that points to a local file.",
                                 self.filename,
                                 line=self.line,
                                 context=self.context)
            elif ((not type_ or
                   type_ not in SAFE_IFRAME_TYPES) and
                  remote_src):
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "iframe_type_unsafe"),
                                 "Typeless iframes/browsers must be local.",
                                 "iframe and browser elements that lack a type "
                                 "attribute must always have src attributes "
                                 "that reference local resources.",
                                 self.filename,
                                 line=self.line,
                                 context=self.context)

        elif tag == "script" and self.extension == "xul":
            # Per the Addon Validator Spec (v2), scripts in XUL
            # must not be remote.

            src = None
            for attr in attrs:
                if attr[0].lower() == "src":
                    src = attr[1].lower()
                    break

            if src:
                if not self._is_url_local(src):
                    self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag",
                                "banned_remote_scripts"),
                        warning="Scripts must not be remote in XUL",
                        description="In XUL, <script> tags must not be "
                                    "referenced to script files that are "
                                    "hosted remotely.",
                        filename=self.filename,
                        line=self.line,
                        context=self.context)
                else:
                    self.found_scripts.add(src)

        # Find CSS and JS attributes and handle their values like they
        # would otherwise be handled by the standard parser flow.
        for attr in attrs:
            attr_name, attr_value = attr[0].lower(), attr[1]

            if (attr_name == "xmlns:xbl" and
                attr_value == "http://www.mozilla.org/xbl"):
                self.xbl = True

            # Test that an absolute URI isn't referenced in Jetpack 1.4.
            if (self.is_jetpack and
                attr_value.startswith("resource://") and
                "-data/" in attr_value):
                self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag", "jetpack_abs_uri"),
                        warning="Absolute URI referenced in Jetpack 1.4",
                        description=["As of Jetpack 1.4, absolute URIs are no "
                                     "longer allowed within add-ons.",
                                     "See %s for more information." %
                                         JETPACK_URI_URL],
                        filename=self.filename,
                        line=self.line,
                        context=self.context,
                        compatibility_type="error")

            if (self.err.detected_type == PACKAGE_THEME and
                attr_value.startswith(("data:", "javascript:"))):

                self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag",
                                "theme_attr_prefix"),
                        warning="Attribute contains banned prefix",
                        description=["A mark element's attribute contains a "
                                     "prefix which is not allowed in themes.",
                                     "Attribute: %s" % attr_name],
                        filename=self.filename,
                        line=self.line,
                        context=self.context)

            if attr_name == "style":
                csstester.test_css_snippet(self.err,
                                           self.filename,
                                           attr_value,
                                           self.line)
            elif attr_name.startswith("on"):  # JS attribute
                # Warn about DOM mutation event handlers.
                if attr_name in DOM_MUTATION_HANDLERS:
                    self.err.warning(
                        err_id=("testcases_markup_markuptester",
                                "handle_starttag",
                                "dom_manipulation_handler"),
                        warning="DOM Mutation Events Prohibited",
                        description="DOM mutation events are flagged because "
                                    "of their deprecated status, as well as "
                                    "their extreme inefficiency. Consider "
                                    "using a different event.",
                        filename=self.filename,
                        line=self.line,
                        context=self.context)

                scripting.test_js_snippet(err=self.err,
                                          data=attr_value,
                                          filename=self.filename,
                                          line=self.line,
                                          context=self.context)

            elif (self.extension == "xul" and
                  attr_name in ("insertbefore", "insertafter") and
                  any((id in attr_value) for id in ("menu_pageSource",
                                                    "menu_pageinspect",
                                                    "javascriptConsole",
                                                    "webConsole"))):
                self.err.notice(
                    err_id=("testcases_markup_markuptester",
                            "handle_starttag",
                            "incompatible_menu_items"),
                    notice="Menu item has been moved",
                    description="Your add-on has an overlay that uses the "
                                "insertbefore or insertafter attribute "
                                "pointing to menuitems that have been moved "
                                "to a different menu item. Your overlay items "
                                "may appear in unexpected locations because "
                                "of this. See "
                        "https://bugzilla.mozilla.org/show_bug.cgi?id=653221"
                                " for more information.",
                    filename=self.filename,
                    line=self.line,
                    context=self.context,
                    for_appversions=FX6_DEFINITION,
                    compatibility_type="warning")


            # Test for generic IDs
            if attr_name == "id" and attr_value in GENERIC_IDS:
                self.err.warning(
                    err_id=("testcases_markup_markuptester",
                            "handle_starttag", "generic_ids"),
                    warning="Overlay contains generically-named IDs",
                    description="An overlay is using a generically-named ID "
                                "that could cause compatibility problems with "
                                "other add-ons. Add-ons must namespace all IDs "
                                "in the overlay, in the same way that "
                                "JavaScript objects must be namespaced.",
                    filename=self.filename,
                    line=self.line,
                    context=self.context)

        # When the dev forgets their <!-- --> on a script tag, bad
        # things happen.
        if "script" in self.xml_state and tag != "script":
            self._save_to_buffer("<" + tag + self._format_args(attrs) + ">")
            return

        self.xml_state.append(orig_tag)
        self.xml_line_stack.append(self.line)
        self.xml_buffer.append(unicode(""))

    def handle_endtag(self, tag):

        tag = tag.lower()
        if tag == "xul:script":
            tag = "script"

        if DEBUG:  # pragma: no cover
            print "E: ", tag, self.xml_state

        if not self.xml_state:
            if "closing_tags" in self.reported or not self.strict:
                if DEBUG:
                    print "Unstrict; extra closing tags ------"
                return
            self.err.warning(("testcases_markup_markuptester",
                              "handle_endtag",
                              "extra_closing_tags"),
                             "Markup parsing error",
                             "The markup file has more closing tags than it "
                             "has opening tags.",
                             self.filename,
                             line=self.line,
                             context=self.context,
                             tier=2)
            self.reported.add("closing_tags")
            if DEBUG:  # pragma: no cover
                print "Too many closing tags ------"
            return

        elif "script" in self.xml_state[:-1]:
            # If we're in a script tag, nothing else matters. Just rush
            # everything possible into the xml buffer.

            self._save_to_buffer("</" + tag + ">")
            if DEBUG:
                print "Markup as text in script ------"
            return

        elif tag not in self.xml_state:
            # If the tag we're processing isn't on the stack, then
            # something is wrong.
            self.err.warning(("testcases_markup_markuptester",
                              "handle_endtag",
                              "extra_closing_tags"),
                             "Parse error: tag closed before opened",
                             ["Markup tags cannot be closed before they are "
                              "opened. Perhaps you were just a little "
                              "overzealous with forward-slashes?",
                              'Tag "%s" closed before it was opened' % tag],
                             self.filename,
                             line=self.line,
                             context=self.context,
                             tier=2)
            if DEBUG:  # pragma: no cover
                print "Tag closed before opened ------"
            return

        data_buffer = self.xml_buffer.pop()
        old_state = self.xml_state.pop()
        old_line = self.xml_line_stack.pop()

        # If the tag on the stack isn't what's being closed and it also
        # classifies as a self-closing tag, we just recursively close
        # down to the level of the tag we're actualy closing.
        if old_state != tag and old_state in SELF_CLOSING_TAGS:
            if DEBUG:
                print "Self closing tag cascading down ------"
            return self.handle_endtag(tag)

        # If this is an XML-derived language, everything must nest
        # properly. No overlapping tags.
        if (old_state != tag and
            self.extension[0] == 'x' and
            not self.strict):

            self.err.warning(("testcases_markup_markuptester",
                              "handle_endtag",
                              "invalid_nesting"),
                             "Markup invalidly nested",
                             "It has been determined that the document "
                             "invalidly nests its tags. This is not permitted "
                             "in the specified document type.",
                             self.filename,
                             line=self.line,
                             context=self.context,
                             tier=2)
            if DEBUG:  # pragma: no cover
                print "Invalid markup nesting ------"

        data_buffer = data_buffer.strip()

        # Perform analysis on collected data.
        if data_buffer:
            if tag == "script":
                scripting.test_js_snippet(err=self.err, data=data_buffer,
                                          filename=self.filename,
                                          line=old_line, context=self.context)
            elif tag == "style":
                csstester.test_css_file(self.err, self.filename, data_buffer,
                                        old_line)

    def handle_data(self, data):
        self._save_to_buffer(data)

    def handle_comment(self, data):
        self._save_to_buffer(data)

    def parse_marked_section(self, i, report=0):
        rawdata = self.rawdata
        _markedsectionclose = re.compile(r']\s*]\s*>')

        assert rawdata[i:i + 3] == '<![', \
               "unexpected call to parse_marked_section()"

        sectName, j = self._scan_name(i + 3, i)
        if j < 0:  # pragma: no cover
            return j
        if sectName in ("temp", "cdata", "ignore", "include", "rcdata"):
            # look for standard ]]> ending
            match = _markedsectionclose.search(rawdata, i + 3)
        else:  # pragma: no cover
            self.error('unknown status keyword %r in marked section' %
                       rawdata[i + 3:j])
        if not match:  # pragma: no cover
            return -1
        if report:  # pragma: no cover
            j = match.start(0)
            self.unknown_decl(rawdata[i + 3: j])
        return match.end(0)

    def _save_to_buffer(self, data):
        """Save data to the XML buffer for the current tag."""

        # We're not interested in data that isn't in a tag.
        if not self.xml_buffer:
            return

        data = unicodehelper.decode(data)

        self.xml_buffer[-1] += data

    def _format_args(self, args):
        """Formats a dict of HTML attributes to be in HTML attribute
        format."""

        if not args:
            return ""

        output = []
        for attr in args:
            output.append(attr[0] + '="' + attr[1] + '"')

        return " " + " ".join(output)

    def _is_url_local(self, url):

        if url.startswith("chrome://"):
            return True

        pattern = re.compile("(ht|f)tps?://")

        return not pattern.match(url)

    # Code to fix for Python issue 670664

    def parse_starttag(self, i):
        self.__starttag_text = None
        endpos = self.check_for_whole_start_tag(i)
        if endpos < 0:
            return endpos
        rawdata = self.rawdata
        self.__starttag_text = rawdata[i:endpos]

        # Now parse the data between i+1 and j into a tag and attrs
        attrs = []
        match = htmlparser.tagfind.match(rawdata, i+1)
        assert match, 'unexpected call to parse_starttag()'
        k = match.end()
        self.lasttag = tag = rawdata[i+1:k].lower()

        while k < endpos:
            m = htmlparser.attrfind.match(rawdata, k)
            if not m:
                break
            attrname, rest, attrvalue = m.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif attrvalue[:1] == '\'' == attrvalue[-1:] or \
                 attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
                attrvalue = self.unescape(attrvalue)
            attrs.append((attrname.lower(), attrvalue))
            k = m.end()

        end = rawdata[k:endpos].strip()
        if end not in (">", "/>"):
            lineno, offset = self.getpos()
            if "\n" in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count("\n")
                offset = len(self.__starttag_text) \
                         - self.__starttag_text.rfind("\n")
            else:
                offset = offset + len(self.__starttag_text)
            self.error("junk characters in start tag: %r"
                       % (rawdata[k:endpos][:20],))
        if end.endswith('/>'):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            if tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)
        return endpos

    def parse_endtag(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i+2] == "</", "unexpected call to parse_endtag"
        match = htmlparser.endendtag.search(rawdata, i+1) # >
        if not match:
            return -1
        j = match.end()
        match = htmlparser.endtagfind.match(rawdata, i) # </ + tag + >
        if not match:
            if self.cdata_tag is not None:
                self.handle_data(rawdata[i:j])
                return j
            self.error("bad end tag: %r" % (rawdata[i:j],))
        tag = match.group(1).strip()

        if self.cdata_tag is not None and tag.lower() != self.cdata_tag:
            self.handle_data(rawdata[i:j])
            return j

        self.handle_endtag(tag.lower())
        self.clear_cdata_mode()
        return j

    def set_cdata_mode(self, tag):
        self.interesting = htmlparser.interesting_cdata
        self.cdata_tag = None

