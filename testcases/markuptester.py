try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""
    
    def __init__(self, err):
        HTMLParser.__init__(self)
        self.err = err
        self.line = 1
        
    def process(self, filename, data, extension="xul"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""
        
        
        self.filename = filename
        self.extension = extension
        
        lines = data.split("\n")
        try:
            for line in lines:
                self.feed(line + "\n")
                self.line += 1
        except:
            self.err.error("Makrup parsing error",
                            """There was an error parsing the markup
                            document.""",
                            self.filename,
                            self.line)
        
    def handle_starttag(self, tag, attrs):
        
        unsafe_tags = ("script",
                       "object",
                       "embed")
        unsafe_tag_pattern = "Unsafe tag (%s) found in %s."
        
        if tag in unsafe_tags:
            self.err.error(unsafe_tag_pattern % (tag, self.filename),
                           """A tag in your markup has been marked as
                           being potentially unsafe. Consider alternate
                           means of accomplishing what the code
                           executed by this tag performs.""",
                           self.filename,
                           self.line)
        elif tag == "iframe":
            # Bork if XUL iframe has no type attribute
            if self.extension == "xul" and \
               "type" not in attrs:
                self.err.error("<iframe>s must have a type attribute.",
                               """All iframe elements must have type
                               attributes.""",
                               self.filename,
                               self.line)
                
                
        
