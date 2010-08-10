
import re
try:
    from HTMLParser import HTMLParser
except ImportError: # pragma: no cover
    from html.parser import HTMLParser

from validator.testcases.markup import csstester
from validator.constants import *

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

class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""
    
    def __init__(self, err, debug=False):
        HTMLParser.__init__(self)
        self.err = err
        self.line = 0
        self.debug = debug
        
        self.xml_state = []
        self.xml_buffer = []
        
        self.reported = {}
        
    def process(self, filename, data, extension="xul"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""
        
        
        self.filename = filename
        self.extension = extension
        
        self.reported = {}
        
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
                        search_line = post_cdata[post_cdata.find("]]>")+3:]
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
        
        try:
            self.feed(line + "\n")
        except Exception as inst:
            if DEBUG: # pragma: no cover
                print self.xml_state, inst
            
            if "markup" in self.reported:
                return
            
            if "script" in self.xml_state or (
               self.debug and "testscript" in self.xml_state):
                if "script_comments" in self.reported:
                    return
                self.err.info(("testcases_markup_markuptester",
                               "_feed",
                               "missing_script_comments"),
                              "Missing comments in <script> tag",
                              """Markup parsing errors occurred
                              while trying to parse the file. This
                              can likely be mitigated by wrapping
                              <script> tag contents in HTML comment
                              tags (<!-- -->)""",
                              self.filename,
                              self.line)
                self.reported["script_comments"] = True
                return
            
            self.err.warning(("testcases_markup_markuptester",
                              "_feed",
                              "parse_error"),
                             "Markup parsing error",
                             ["""There was an error parsing the markup
                              document.""",
                              str(inst)],
                             self.filename,
                             self.line)
            self.reported["markup"] = True
        
    
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
        
        if DEBUG: # pragma: no cover
            print self.xml_state, tag, self_closing
        
        # A fictional tag for testing purposes.
        if tag == "xbannedxtestx":
            self.err.error(("testcases_markup_markuptester",
                            "handle_starttag",
                            "banned_element"),
                           "Banned element",
                           "A banned element was detected",
                           self.filename,
                           self.line)
        
        if self.err.detected_type == PACKAGE_LANGPACK:
            
            if tag in UNSAFE_TAGS:
                self.err.error(("testcases_markup_markuptester",
                                "handle_starttag",
                                "unsafe_langpack"),
                               "Unsafe tag in language pack",
                               ["""A tag in your markup has been marked
                                as being potentially unsafe. Consider
                                alternate means of accomplishing what
                                the code executed by this tag
                                performs.""",
                                'Tag "%s" is disallowed.' % tag],
                               self.filename,
                               self.line)
                if DEBUG: # pragma: no cover
                    print "Unsafe Tag ------"
            
            # Make sure all src/href attributes are local
            for attr in attrs:
                if attr[0].lower() in ("src", "href") and \
                   not self._is_url_local(attr[1].lower()):
                    self.err.error(("testcases_markup_markuptester",
                                    "handle_starttag",
                                    "remote_src_href"),
                                   "src/href attributes must be local.",
                                   """Language packs require that all
                                   src/href attributes must begin with
                                   'chrome://'""",
                                   self.filename,
                                   self.line)
        
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
            if isinstance(src, str):
                remote_src = not self._is_url_local(src)
                
            if type_ and \
               not (type_ in SAFE_IFRAME_TYPES or 
                    not remote_src):
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "iframe_type_unsafe"),
                                 "iframe missing 'type' attribute",
                                 """All iframe elements must have
                                 either a valid `type` attribute or
                                 a `src` attribute that points to a
                                 local file.""",
                                 self.filename,
                                 self.line)
            elif (not type_ or 
                  type_ not in SAFE_IFRAME_TYPES) and \
                 remote_src:
                self.err.warning(("testcases_markup_markuptester",
                                  "handle_starttag",
                                  "iframe_type_unsafe"),
                                 "Typeless iframes must be local.",
                                 """iframe elements that lack a
                                 type attribute must always have
                                 src attributes that reference
                                 local resources.""",
                                 self.filename,
                                 self.line)
            
        elif tag == "script" and self.extension == "xul":
            # Per the Addon Validator Spec (v2), scripts in XUL
            # must not be remote.
            
            src = None
            for attr in attrs:
                if attr[0].lower() == "src":
                    src = attr[1].lower()
            
            if src and not self._is_url_local(src):
                self.err.error(("testcases_markup_markuptester",
                                "handle_starttag",
                                "banned_remote_scripts"),
                               "Scripts must not be remote in XUL",
                               """In XUL, <script> tags must not be
                               referenced to script files that are
                               hosted remotely.""",
                               self.filename,
                               self.line)
        
        # Find CSS and JS attributes and handle their values like they
        # would otherwise be handled by the standard parser flow.
        for attr in attrs:
            if attr[0].lower() == "style":
                csstester.test_css_snippet(self.err,
                                           self.filename,
                                           attr[1],
                                           self.line)
        
        # When the dev forgets their <!-- --> on a script tag, bad
        # things happen.
        if "script" in self.xml_state and tag != "script":
            self._save_to_buffer("<" + tag +
                                 self._format_args(attrs) + ">")
            return
        
        self.xml_state.append(tag)
        self.xml_buffer.append("")
        
    def handle_endtag(self, tag):
        
        tag = tag.lower()
        
        if DEBUG: # pragma: no cover
            print tag, self.xml_state
        
        if not self.xml_state:
            if "closing_tags" in self.reported:
                return
            self.err.error(("testcases_markup_markuptester",
                            "handle_endtag",
                            "extra_closing_tags"),
                           "Markup parsing error",
                           """The markup file has more closing tags
                           than it has opening tags.""",
                           self.filename,
                           self.line)
            self.reported["closing_tags"] = True
            if DEBUG: # pragma: no cover
                print "Too many closing tags ------"
            return
            
        elif "script" in self.xml_state:
            # If we're in a script tag, nothing else matters. Just rush
            # everything possible into the xml buffer.
            
            self._save_to_buffer("</" + tag + ">")
            return
            
        elif tag not in self.xml_state:
            # If the tag we're processing isn't on the stack, then
            # something is wrong.
            self.err.warning(("testcases_markup_markuptester",
                              "handle_endtag",
                              "extra_closing_tags"),
                             "Parse error: tag closed before opened",
                             ["""Markup tags cannot be closed before
                              they are opened. Perhaps you were just a
                              little overzealous with forward-slashes?""",
                              'Tag "%s" closed before it was opened' % tag],
                             self.filename,
                             self.line)
            if DEBUG: # pragma: no cover
                print "Tag closed before opened ------"
            return
        
        data_buffer = self.xml_buffer.pop()
        old_state = self.xml_state.pop()
        
        # If the tag on the stack isn't what's being closed and it also
        # classifies as a self-closing tag, we just recursively close
        # down to the level of the tag we're actualy closing.
        if old_state != tag and old_state in SELF_CLOSING_TAGS:
            return self.handle_endtag(tag)
            
        # If this is an XML-derived language, everything must nest
        # properly. No overlapping tags.
        if old_state != tag and self.extension[0] == 'x':
            self.err.error(("testcases_markup_markuptester",
                            "handle_endtag",
                            "invalid_nesting"),
                           "Markup invalidly nested",
                           """It has been determined that the document
                           invalidly nests its tags. This is not
                           permitted in the specified document type.""",
                           self.filename,
                           self.line)
            if DEBUG: # pragma: no cover
                print "Invalid markup nesting ------"
        
        # Perform analysis on collected data.
        if tag == "script":
            # TODO: Link up the JS analysis module once it's written.
            pass
        elif tag == "style":
            csstester.test_css_file(self.err,
                                    self.filename,
                                    data_buffer,
                                    self.line)
        
        # TODO : Handle script attribute values
        
    def handle_data(self, data):
        self._save_to_buffer(data)
        
    def handle_comment(self, data):
        self._save_to_buffer(data)
        
    def parse_marked_section(self, i, report=0):
        rawdata= self.rawdata
        _markedsectionclose = re.compile(r']\s*]\s*>')
        
        assert rawdata[i:i+3] == '<![', "unexpected call to parse_marked_section()"
        sectName, j = self._scan_name( i+3, i )
        if j < 0: #pragma: no cover
            return j
        if sectName in ("temp", "cdata", "ignore", "include", "rcdata"):
            # look for standard ]]> ending
            match= _markedsectionclose.search(rawdata, i+3)
        else: #pragma: no cover
            self.error('unknown status keyword %r in marked section' % rawdata[i+3:j])
        if not match: #pragma: no cover
            return -1
        if report: #pragma: no cover
            j = match.start(0)
            self.unknown_decl(rawdata[i+3: j])
        return match.end(0)
        
    def _save_to_buffer(self, data):
        """Save data to the XML buffer for the current tag."""
        
        # We're not interested in data that isn't in a tag.
        if not self.xml_buffer:
            return
        
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
        
