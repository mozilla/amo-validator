try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

PACKAGE_ANY = 0
PACKAGE_EXTENSION = 1
PACKAGE_THEME = 2
PACKAGE_DICTIONARY = 3
PACKAGE_LANGPACK = 4
PACKAGE_SEARCHPROV = 5
PACKAGE_MULTI = 1
PACKAGE_SUBPACKAGE = 7

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
UNSAFE_TAG_PATTERN = "Unsafe tag (%s) found in language pack"
UNSAFE_IF_TYPE = 'iframe cannot have type="%s"'
TAG_NOT_OPENED = "Tag (%s) being closed before it is opened."

class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""
    
    def __init__(self, err):
        HTMLParser.__init__(self)
        self.err = err
        self.line = 0
        
        self.xml_state = []
        self.xml_buffer = []
        
        self.alerted_script_comments = False
        
    def process(self, filename, data, extension="xul"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""
        
        
        self.filename = filename
        self.extension = extension
        
        reported = False
        
        lines = data.split("\n")
        for line in lines:
            try:
                self.line += 1
                self.feed(line + "\n")
            except Exception as inst:
                
                if DEBUG:
                    print self.xml_state, inst
                
                if reported:
                    continue
                
                if "script" in self.xml_state:
                    print "script"
                    if self.alerted_script_comments:
                        continue
                    self.err.info("Missing comments in <script> tag",
                                  """Markup parsing errors occurred
                                  while trying to parse the file. This
                                  can likely be mitigated by wrapping
                                  <script> tag contents in HTML comment
                                  tags (<!-- -->)""",
                                  self.filename,
                                  self.line)
                    self.alerted_script_comments = True
                    continue
                
                self.err.warning("Markup parsing error",
                                 """There was an error parsing the
                                 markup document.""",
                                 self.filename,
                                 self.line)
                reported = True
        
    
    def handle_startendtag(self, tag, attrs):
        # Self closing tags don't have an end tag, so we want to
        # completely cut out the references to handle the end tag.
        self.handle_starttag(tag, attrs, True)
        self.handle_endtag(tag)
    
    def handle_starttag(self, tag, attrs, self_closing=False):
        
        tag = tag.lower()
        
        # Be extra sure it's not a self-closing tag.
        if not self_closing:
            self_closing = tag in SELF_CLOSING_TAGS
        
        if DEBUG:
            print self.xml_state, tag, self_closing
        
        # A fictional tag for testing purposes.
        if tag == "xbannedxtestx":
            self.err.error("Banned element",
                           "A banned element was detected",
                           self.filename,
                           self.line)
        
        if self.err.detected_type == PACKAGE_LANGPACK:
            
            if tag in UNSAFE_TAGS:
                self.err.error(UNSAFE_TAG_PATTERN % tag,
                               """A tag in your markup has been marked
                               as being potentially unsafe. Consider
                               alternate means of accomplishing what
                               the code executed by this tag
                               performs.""",
                               self.filename,
                               self.line)
            
            # Make sure all src/href attributes are local
            for attr in attrs:
                if attr[0].lower() in ("src", "href") and \
                   not attr[1].lower().startswith("chrome://"):
                    self.err.error("src/href elements must be local.",
                                   """Language packs require that all
                                   src/href attributes must begin with
                                   'chrome://'""",
                                   self.filename,
                                   self.line)
        
        if tag == "iframe":
            # Bork if XUL iframe has no type attribute
            if self.extension == "xul":
                
                type_ = None
                for attr in attrs:
                    if attr[0].lower() == "type":
                        type_ = attr[1].lower()
                
                if type_ is None:
                    self.err.warning("iframe missing 'type' attribute",
                                     """All iframe elements must have
                                     type attributes.""",
                                     self.filename,
                                     self.line)
                elif type_ not in SAFE_IFRAME_TYPES:
                    self.err.error(UNSAFE_IF_TYPE % attrs["type"],
                                   """It is a security risk to use
                                   type="%s" on a XUL iframe.""" %
                                    attrs["type"],
                                   self.filename,
                                   self.line)
        
        # When the dev forgets their <!-- --> on a script tag, bad
        # things happen.
        if "script" in self.xml_state:
            self._save_to_buffer("<" + tag +
                                 self._format_args(attrs) + ">")
            return
        
        self.xml_state.append(tag)
        self.xml_buffer.append("")
        
    def handle_endtag(self, tag):
        
        tag = tag.lower()
        
        if DEBUG:
            print tag, self.xml_state
        
        if not self.xml_state:
            self.err.error("Markup parsing error",
                           """The markup file has more closing tags
                           than it has opening tags.""",
                           self.filename,
                           self.line)
            return
            
        elif "script" in self.xml_state:
            # If we're in a script tag, nothing else matters. Just rush
            # everything possible into the xml buffer.
            
            self._save_to_buffer("</" + tag + ">")
            return
            
        elif tag not in self.xml_state:
            # If the tag we're processing isn't on the stack, then
            # something is wrong.
            self.err.warning(TAG_NOT_OPENED % tag,
                             """Markup tags cannot be closed before
                             they are opened. Perhaps you were just a
                             little overzealous with
                             forward-slashes?""",
                             self.filename,
                             self.line)
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
            self.err.error("Markup invalidly nested",
                           """It has been determined that the document
                           invalidly nests its tags. This is not
                           permitted in the specified document type
                           (%s)""" % self.extension,
                           self.filename,
                           self.line)
        
        
        # Perform analysis on collected data.
        if tag == "script":
            # TODO: Link up the JS analysis module once it's written.
            pass
        elif tag == "style":
            # TODO: Wire up with the CSS analyzer once it's written.
            pass
        
        # TODO : Handle script/CSS attribute values
        
    def handle_data(self, data):
        self._save_to_buffer(data)
        
    def handle_comment(self, data):
        self._save_to_buffer(data)
    
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
