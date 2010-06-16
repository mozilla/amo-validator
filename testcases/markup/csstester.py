import re
import json

import cssutils

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
    
    tokenizer = cssutils.tokenize2.Tokenizer()
    token_generator = tokenizer.tokenize(data)
    
    _run_css_tests(err, token_generator, filename)
    
def _run_css_tests(err, tokens, filename):
    """Processes a CSS file to test it for things that could cause it
    to be harmful to the browser."""
    
    last_descriptor = None
    
    skip_types = ("S", "COMMENT")
    
    for (tok_type, value, line, position) in tokens:
        
        # Save the last descriptor for reference.
        if tok_type == "IDENT":
            last_descriptor = value.lower()
            if value.startswith("-webkit"):
                err.error("Blasphemy.",
                          "WebKit descriptors? Really?",
                          filename,
                          line)
                  
        elif tok_type == "URI":
            
            # If we hit a URI after -moz-binding, we may have a
            # potential security issue.
            if last_descriptor == "-moz-binding":
                # We need to make sure the URI is not remote.
                value = value[4:-1].strip('"')
                
                # Ensure that the resource isn't remote.
                if value.startswith("http"):
                    err.error("Cannot reference external scripts.",
                              """-moz-binding cannot reference external
                              scripts in CSS. This is considered to be
                              a security issue.""",
                              filename,
                              line)
                
    
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
    
