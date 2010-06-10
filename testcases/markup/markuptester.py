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

UNSAFE_TAGS = ("script",
               "object",
               "embed")
SAFE_IFRAME_TYPES = ("content",
                     "content-primary",
                     "content-targetable")
UNSAFE_TAG_PATTERN = "Unsafe tag (%s) found in language pack"
UNSAFE_IF_TYPE = 'iframe cannot have type="%s"'

class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""
    
    def __init__(self, err):
        super.__init__(self)
        self.err = err
        self.line = 0
        
        self.xml_state = []
        self.xml_buffer = []
        
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
            except:
                if reported:
                    continue
                self.err.warning("Markup parsing error",
                                 """There was an error parsing the
                                 markup document.""",
                                 self.filename,
                                 self.line)
                reported = True
        
    def handle_starttag(self, tag, attrs):
        
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
        
        if tag == "iframe":
            # Bork if XUL iframe has no type attribute
            if self.extension == "xul":
                
                if "type" not in attrs:
                    self.err.warning("iframe missing 'type' attribute",
                                     """All iframe elements must have
                                     type attributes.""",
                                     self.filename,
                                     self.line)
                elif attrs["type"] not in SAFE_IFRAME_TYPES:
                    self.err.error(UNSAFE_IF_TYPE % attrs["type"],
                                   """It is a security risk to use
                                   type="%s" on a XUL iframe.""" %
                                    attrs["type"],
                                   self.filename,
                                   self.line)
                                   
        self.xml_state.append(tag)
        self.xml_buffer.append("")
        
    def handle_endtag(self, tag):
        
        if not self.xml_state:
            self.err.error("Markup parsing error",
                           """The markup file has more closing tags
                           than it has opening tags.""",
                           self.filename,
                           self.line)
            return
        
        data_buffer = self.xml_buffer.pop()
        old_state = self.xml_state.pop()
        
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
            pass
        
        
    def handle_data(self, data):
        
        # We're not interested in data that isn't in a tag.
        if not xml_buffer:
            return
        
        # Append the last item in the data buffer with the current data
        xml_buffer[-1] += data

