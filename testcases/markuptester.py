try:
    import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import decorator

@decorator.register_test()
def test_markup_files(err, package_contents=None, xpi_package=None):
    """Iterates through all xml-based markup files and validates their
    contents. """
    
    

class MarkupParser(HTMLParser):
    """Parses and inspects various markup languages"""
    
    def __init(self, err, filename, extension="xul"):
        self.extension = extension
        self.err = err
        
    def handle_starttag(self, tag, attrs):
        
        unsafe_tags = ("script",
                       "object",
                       "embed")
        
        if tag in unsafe_tags:
            self.err.error("Unsafe tag (%s) found in )
        
    def handle_endtag(self, tag):
        