import chardet
import json
import os
import re
import subprocess
import tempfile
from cStringIO import StringIO

import validator.testcases.javascript.traverser as traverser
from validator.constants import SPIDERMONKEY_INSTALLATION
from validator.contextgenerator import ContextGenerator

def test_js_file(err, name, data, filename=None, line=0):
    "Tests a JS file by parsing and analyzing its tokens"
    
    if SPIDERMONKEY_INSTALLATION is None and \
       err.get_resource("SPIDERMONKEY") is None: # Default value is False
        return

    # The filename is 
    if filename is None:
        filename = name
    
    # Get the AST tree for the JS code
    try:
        tree = _get_tree(name,
                         data,
                         shell=(err and err.get_resource("SPIDERMONKEY")) or
                               SPIDERMONKEY_INSTALLATION,
                         errorbundle=err)

    except JSReflectException as exc:
        str_exc = str(exc)
        if "SyntaxError" in str_exc:
            err.error(("testcases_scripting",
                       "test_js_file",
                       "syntax_error"),
                       "Javascript Syntax Error",
                       ["A syntax error in the Javascript halted validation "
                        "of that file.",
                        "Message: %s" % str_exc[15:-1]],
                       filename=filename,
                       line=exc.line,
                       context=ContextGenerator(data))
        else:
            err.error(("testcases_scripting",
                       "test_js_file",
                       "retrieving_tree"),
                      "JS reflection error prevented validation",
                      ["An error in the JavaScript file prevented it from "
                       "being properly read by the Spidermonkey JS engine.",
                       str(exc)],
                      filename=filename)

            import sys
            etype, err, tb = sys.exc_info()
            raise exc, None, tb

        return


    if tree is None:
        return None
    
    # Set the tier to 4 (Security Tests)
    if err is not None:
        before_tier = err.tier
        err.tier = 4

    context = ContextGenerator(data)
    if traverser.DEBUG:
        _do_test(err=err, filename=filename, line=line, context=context,
                 tree=tree)
    else:
        try:
            _do_test(err=err, filename=filename, line=line, context=context,
                     tree=tree)
        except:
            pass
            #print "An error was encountered while attempting to validate a script"

    _regex_tests(err, data, filename)

    # Reset the tier so we don't break the world
    if err is not None:
        err.tier = before_tier

def test_js_snippet(err, data, filename=None, line=0):
    "Process a JS snippet by passing it through to the file tester."
    
    if filename is not None:
        name = "%s:%d" % (filename, line)
    else:
        name = str(line)
    
    # Wrap snippets in a function to prevent the parser from freaking out
    # when return statements exist without a corresponding function.
    data = "(function(){%s\n})()" % data

    test_js_file(err, name, data, filename, line)
    
def _do_test(err, filename, line, context, tree):
    t = traverser.Traverser(err, filename, line, context=context)
    t.run(tree)

def _regex_tests(err, data, filename):

    c = ContextGenerator(data)
    
    np_warning = "Network preferences may not be modified."

    errors = {"globalStorage\\[.*\\].password":
                  "Global Storage may not be used to store passwords.",
              "network\\.http": np_warning,
              "extensions\\.blocklist\\.url": np_warning,
              "extensions\\.blocklist\\.level": np_warning,
              "extensions\\.blocklist\\.interval": np_warning,
              "general\\.useragent": np_warning}

    for regex, message in errors.items():
        reg = re.compile(regex)
        match = reg.search(data)

        if match:
            line = c.get_line(match.start())
            err.error(("testcases_scripting",
                       "regex_tests",
                       "compiled_error"),
                      "Malicious code detected",
                      message,
                      filename=filename,
                      line=line,
                      context=c)


class JSReflectException(Exception):
    "An exception to indicate that tokenization has failed"

    def __init__(self, value):
        self.value = value
        self.line = None

    def __str__(self):
        return repr(self.value)

    def line_num(self, line_num):
        "Set the line number and return self for chaining"
        self.line = int(line_num)
        return self

def is_ctrl_char(x):
    "Returns whether X is an ASCII control character"
    y = ord(x)
    return 0 <= y <= 31 and y not in (9, 10, 13) # TAB, LF, CR

def strip_weird_chars(chardata, err=None, name=""):
    line_num = 1
    out_code = StringIO()
    has_warned_ctrlchar = False

    for line in chardata.split("\n"):

        charpos = 0
        for char in line:
            if not is_ctrl_char(char):
                out_code.write(char)
            else:
                if not has_warned_ctrlchar and err is not None:
                    err.warning(("testcases_scripting",
                                 "_get_tree",
                                 "control_char_filter"),
                                "Invalid character in JS file",
                                "An invalid character (ASCII 0-31, except CR "
                                "and LF) has been found in a JS file. These "
                                "are considered unsafe and should be removed.",
                                filename=name,
                                line=line_num,
                                column=charpos,
                                context=ContextGenerator(chardata))
                has_warned_ctrlchar = True

            charpos += 1

        out_code.write("\n")
        line_num += 1

    return out_code.getvalue()

def _get_tree(name, code, shell=SPIDERMONKEY_INSTALLATION, errorbundle=None):
    "Returns an AST tree of the JS passed in `code`."
    
    if not code:
        return None

    encoding = None
    try:
        code = unicode(code) # Make sure we can get a Unicode representation
        
        code = strip_weird_chars(code, errorbundle, name=name)
        data = json.dumps(code)
    except UnicodeDecodeError:
        # If it's not an easily decodeable encoding, detect it and decode that
        encoding = chardet.detect(code)["encoding"].lower()
        if any([is_ctrl_char(x) for x in code]):
            raise JSReflectException("Invalid encoding; control character")
        data = json.dumps(code, encoding=encoding)

    data = """try{
        print(JSON.stringify(Reflect.parse(%s)));
    } catch(e) {
        print(JSON.stringify({
            "error":true,
            "error_message":e.toString(),
            "line_number":e.lineNumber
        }));
    }""" % data

    # Push the data to a temporary file
    temp = tempfile.NamedTemporaryFile(mode="w+", delete=True)
    temp.write(data)
    temp.flush() # This is very important

    cmd = [shell, "-f", temp.name]
    shell = subprocess.Popen(cmd,
	                     shell=False,
			     stderr=subprocess.PIPE,
			     stdout=subprocess.PIPE)
    data, stderr = shell.communicate()
    if stderr:
        raise RuntimeError('Error calling %r: %s' % (cmd, stderr))

    # Closing the temp file will delete it.
    temp.close()

    ## Strip weird chars again; it doesn't hurt the analyzer and it prevents
    ## devs from hiding bad unicode characters in their JS.
    #data = strip_weird_chars(data, errorbundle, name)
    #for escapechar in ("\\x", "\\u"):
    #    data = data.replace(escapechar, "")
    data = unicode(data)
    parsed = json.loads(data, encoding=encoding, strict=False) # Encoding defaults to None

    if "error" in parsed and parsed["error"]:
        if parsed["error_message"][:14] == "ReferenceError":
            raise RuntimeError("Spidermonkey version too old; "
                               "1.8pre+ required")
        else:
            raise JSReflectException(parsed["error_message"]).line_num(
                    parsed["line_number"])

    return parsed

