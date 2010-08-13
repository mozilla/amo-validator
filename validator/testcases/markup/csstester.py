import re
import json
import fnmatch

import cssutils

def test_css_file(err, filename, data, line_start=1):
    "Parse and test a whole CSS file."
    
    tokenizer = cssutils.tokenize2.Tokenizer()
    token_generator = tokenizer.tokenize(data)
    
    try:
        _run_css_tests(err, token_generator, filename, line_start - 1)
    except: #pragma: no cover
        # This happens because tokenize is a generator.
        # Bravo, Mr. Bond, Bravo.
        err.error(("testcases_markup_csstester",
                   "test_css_file",
                   "could_not_parse"),
                  "Could not parse CSS file",
                  "CSS file could not be parsed by the tokenizer.",
                  filename)
        #raise
        return
        
    
def test_css_snippet(err, filename, data, line):
    "Parse and test a CSS nugget."
    
    # Re-package to make it CSS-complete
    data = "#foo{%s}" % data
    
    test_css_file(err, filename, data, line)
    
def _run_css_tests(err, tokens, filename, line_start=0):
    """Processes a CSS file to test it for things that could cause it
    to be harmful to the browser."""
    
    last_descriptor = None
    
    skip_types = ("S", "COMMENT")
    
    webkit_insts = []
    identity_box_mods = []
    unicode_errors = []
    
    while True:
        
        try:
            (tok_type, value, line, position) = tokens.next()
        except UnicodeDecodeError:
            unicode_errors.append(str(line + line_start))
            continue
        except StopIteration:
            break
        except Exception, e:
            # Comment me out for debug!
            raise
            
            print type(e), e
            print filename
            print line + line_start
            continue
        
        # Save the last descriptor for reference.
        if tok_type == "IDENT":
            last_descriptor = value.lower()
            if value.startswith("-webkit"):
                webkit_insts.append(str(line + line_start))
                  
        elif tok_type == "URI":
            
            # If we hit a URI after -moz-binding, we may have a
            # potential security issue.
            if last_descriptor == "-moz-binding":
                # We need to make sure the URI is not remote.
                value = value[4:-1].strip('"\'')
                
                # Ensure that the resource isn't remote.
                # TODO : This might need to be chrome://*/content/*
                if not fnmatch.fnmatch(value, "chrome://*"):
                    if not fnmatch.fnmatch(value, "*tp*"):
                        err.warning(("testcases_markup_csstester",
                                     "_run_css_tests",
                                     "-moz-binding_external"),
                                    "Non-chrome:// -moz-binding found.",
                                    """-moz-binding descriptors should always
                                    be chrome:// URLs. They should not be
                                    used with relative file paths.""",
                                    filename,
                                    line + line_start)
                    else:
                        err.error(("testcases_markup_csstester",
                                   "_run_css_tests",
                                   "-moz-binding_external"),
                                  "Cannot reference external scripts.",
                                  """-moz-binding cannot reference external
                                  scripts in CSS. This is considered to be a
                                  security issue. The script file must be
                                  placed in the /content/ directory of the
                                  package.""",
                                  filename,
                                  line + line_start)
            
        elif tok_type == "HASH":
            # Search for interference with the identity box.
            if value == "#identity-box":
                identity_box_mods.append(str(line + line_start))
    
    if identity_box_mods:
        err.warning(("testcases_markup_csstester",
                    "_run_css_tests",
                    "identity_box"),
                    "Modification to identity box.",
                    ["""The identity box (#identity-box) is a
                     sensitive piece of the interface and should
                     not be modified.""",
                     "Lines: %s" % ", ".join(identity_box_mods)],
                filename)
    if webkit_insts:
        err.error(("testcases_markup_csstester",
                   "_run_css_tests",
                   "webkit"),
                  "Blasphemy.",
                  ["WebKit descriptors? Really?"
                   "Nonsense found on lines: %s" % ", ".join(webkit_insts)],
                  filename)
    if unicode_errors:
        err.info(("testcases_markup_csstester",
                  "test_css_file",
                  "unicode_decode"),
                 "Unicode decode error.",
                 ["""While decoding a CSS file, an unknown character
                  was encountered, causing some problems.""",
                  "Lines: %s" % ", ".join(unicode_errors)],
                 filename)
