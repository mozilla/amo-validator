import re
import logging

import cssutils
from cssutils import CSSParser

CSS_CURRENT_ERR = None
CSS_CURRENT_FILE = ""

def _fetcher(url):
    "Tells the CSS parser not to pull in imports."
    
    _test_url(url)
    
    return (None, '/* no thanks :) */')
    

def test_css_file(err, filename, data):
    "Parse and test a whole CSS file."
    
    global CSS_CURRENT_ERR, CSS_CURRENT_FILE
    CSS_CURRENT_ERR = err
    CSS_CURRENT_FILE = filename
    
    cssutils.log.setLevel(logging.FATAL)
    
    parser = CSSParser(raiseExceptions=False)
    parser.setFetcher(_fetcher)
    
    sheet = parser.parseString(data)
    _run_css_tests(sheet, filename)
    
def _run_css_tests(sheet, filename):
    """Processes a CSS file to test it for things that could cause it
    to be harmful to the browser."""
    
    urls = cssutils.getUrls(sheet)
    
    for url in urls:
        _test_url(url)
    

def _handle_error():
    "Handles CSS errors"

def _test_url(url):
    "Tests a URL to make sure it isn't remote."
    
    global CSS_CURRENT_ERR
    
    unsuitable_url = re.compile("https?:")
    
    if unsuitable_url.match(url):
        CSS_CURRENT_ERR.error("@import statements may not be remote.",
                              """When importing CSS, the @import
                              statement may not reference remote CSS
                              resources.""",
                              CSS_CURRENT_FILE)
    
