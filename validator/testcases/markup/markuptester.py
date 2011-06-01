import re
import sys
import types
try:
    from HTMLParser import HTMLParser
except ImportError:  # pragma: no cover
    from html.parser import HTMLParser

import validator.testcases.scripting as scripting
import validator.unicodehelper as unicodehelper
from validator.testcases.markup import csstester
from validator.contextgenerator import ContextGenerator
from validator.constants import *
from validator.decorator import versions_after

DEBUG = False

UNSAFE_TAGS = ("script",
               "object",
               "embed",
               "base")
SELF_CLOSING_TAGS = ("area",
                     "base",
                     "basefont",
                     "br",
                     "col",
                     "frame",
                     "hr",
                     "img",
                     "input",
                     "li",
                     "link",
                     "meta",
                     "p",
                     "param")
SAFE_IFRAME_TYPES = ("content",
                     "content-primary",
                     "content-targetable")
TAG_NOT_OPENED = "Tag (%s) being closed before it is opened."

DOM_MUTATION_HANDLERS = ("ondomattrmodified", "ondomattributenamechanged",
     "ondomcharacterdatamodified", "ondomelementnamechanged",
     "ondomnodeinserted", "ondomnodeinsertedintodocument", "ondomnoderemoved",
     "ondomnoderemovedfromdocument", "ondomsubtreemodified")


class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""

    def __init__(self, err, strict=True, debug=False):
        HTMLParser.__init__(self)
        self.err = err
        self.line = 0
        self.strict = strict
        self.debug = debug

        self.context = None

        self.xml_state = []
        self.xml_buffer = []

        self.reported = set()

    def process(self, filename, data, extension="xul"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""

        self.filename = filename
        self.extension = extension.lower()

        self.reported = set()

        self.context = ContextGenerator(data)

        lines = data.split("\n")
        line_buffer = []
        force_buffer = False
        for line in lines:
            self.line += 1

            search_line = line
            while True:
                # CDATA elements are gross. Pass the whole entity as one chunk
                if "<![CDATA[" in search_line and not force_buffer:
                    cdatapos = search_line.find("<![CDATA[")
                    post_cdata = search_line[cdatapos:]

                    if "]]>" in post_cdata:
                        search_line = post_cdata[post_cdata.find("]]>") + 3:]
                        continue
                    force_buffer = True
                elif "]]>" in search_line and force_buffer:
                    force_buffer = False
                break

            if force_buffer:
                line_buffer.append(line)
            else:
                if line_buffer:
                    line_buffer.append(line)
                    line = "\n".join(line_buffer)
                    line_buffer = []
                self._feed_parser(line)

    def _feed_parser(self, line):
        "Feeds data into the parser"

        line = unicodehelper.decode(line)

        try:
            self.feed(line + "\n")
        except UnicodeDecodeError, exc_instance:
            exc_class, val, traceback = sys.exc_info()
            try:
                line = line.decode("ascii", "ignore")
                self.feed(line + "\n")
            except:
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
                                context=self.context)
                self.reported.add("script_comments")
                return

            if self.strict:
                self.err.warning(("testcases_markup_markuptester",
                                  "_feed",
                                  "parse_error"),
                                 "Markup parsing error",
                                 ["There was an error parsing the markup "
                                  "document.",
                                  str(inst)],
                                 self.filename,
                                 line=self.line,
                                 context=self.context)
            self.reported.add("markup")

    def handle_startendtag(self, tag, attrs):
        # Self closing tags don't have an end tag, so we want to
        # completely cut out the references to handle the end tag.
        self.handle_starttag(tag, attrs, True)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs, self_closing=False):

        # Normalize!
        tag = tag.lower()

        # Be extra sure it's not a self-closing tag.
        if not self_closing:
            self_closing = tag in SELF_CLOSING_TAGS

        if DEBUG:  # pragma: no cover
            print "S: ", self.xml_state, tag, self_closing

        # A fictional tag for testing purposes.
        if tag == "xbannedxtestx":
            self.err.error(("testcases_markup_markuptester",
                            "handle_starttag",
                            "banned_element"),
                           "Banned element",
                           "A banned element was detected",
                           self.filename,
                           line=self.line,
                           context=self.context)

        if self.err.detected_type == PACKAGE_LANGPACK:

            if tag in UNSAFE_TAGS:
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "unsafe_langpack"),
                                 "Unsafe tag in language pack",
                                 ["A tag in your markup has been marked as "
                                  "being potentially unsafe. Consider "
                                  "alternate means of accomplishing what the "
                                  "code executed by this tag performs.",
                                  'Tag "%s" is disallowed.' % tag],
                                 self.filename,
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
                    self.err.reject = True

        if tag in ("iframe", "browser") and self.extension == "xul":
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

            if type_ and \
               not (type_ in SAFE_IFRAME_TYPES or
                    not remote_src):
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
            elif (not type_ or
                  type_ not in SAFE_IFRAME_TYPES) and \
                 remote_src:
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

            if src and not self._is_url_local(src):
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "banned_remote_scripts"),
                                 "Scripts must not be remote in XUL",
                                 "In XUL, <script> tags must not be referenced "
                                 "to script files that are hosted remotely.",
                                 self.filename,
                                 line=self.line,
                                 context=self.context)

        # Find CSS and JS attributes and handle their values like they
        # would otherwise be handled by the standard parser flow.
        for attr in attrs:
            attr_name = attr[0].lower()
            if attr_name == "style":
                csstester.test_css_snippet(self.err,
                                           self.filename,
                                           attr[1],
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
                                          data=attr[1],
                                          filename=self.filename)

            elif (self.extension == "xul" and
                  attr_name in ("insertbefore", "insertafter") and
                  any((id in attr[1]) for id in ("menu_pageSource",
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
                    for_appversions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                                         versions_after("firefox", "6.0a1")},
                    compatibility_type="warning")


        # When the dev forgets their <!-- --> on a script tag, bad
        # things happen.
        if "script" in self.xml_state and tag != "script":
            self._save_to_buffer("<" + tag + self._format_args(attrs) + ">")
            return

        self.xml_state.append(tag)
        self.xml_buffer.append(unicode(""))

    def handle_endtag(self, tag):

        tag = tag.lower()

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
                             context=self.context)
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
                             context=self.context)
            if DEBUG:  # pragma: no cover
                print "Tag closed before opened ------"
            return

        data_buffer = self.xml_buffer.pop()
        old_state = self.xml_state.pop()

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
                             context=self.context)
            if DEBUG:  # pragma: no cover
                print "Invalid markup nesting ------"

        data_buffer = data_buffer.strip()

        # Perform analysis on collected data.
        if data_buffer:
            if tag == "script":
                scripting.test_js_snippet(self.err,
                                          data_buffer,
                                          self.filename,
                                          self.line)
            elif tag == "style":
                csstester.test_css_file(self.err,
                                        self.filename,
                                        data_buffer,
                                        self.line)

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

