import re
import json
import fnmatch

import cssutils

def test_css_file(err, filename, data):
    "Parse and test a whole CSS file."
    
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
                if not fnmatch.fnmatch(value, "chrome://*/content/*"):
                    err.error("Cannot reference external scripts.",
                              """-moz-binding cannot reference external
                              scripts in CSS. This is considered to be
                              a security issue. The script file must be
                              placed in the /content/ directory of the
                              package.""",
                              filename,
                              line)
            
        elif tok_type == "HASH":
            
            if value == "#identity-box":
                
                err.warning("Modification to identity box.",
                            """The identity box (#identity-box) is a
                            sensitive piece of the interface and should
                            not be modified.""",
                            filename,
                            line)
    
