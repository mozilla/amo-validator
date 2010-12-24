import chardet
import json
import os
import re
import subprocess
import tempfile

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
        tree = _get_tree(name, data, (err and
                                      err.get_resource("SPIDERMONKEY")) or
                                     SPIDERMONKEY_INSTALLATION)
    except JSReflectException:
        err.error(("testcases_scripting",
                   "test_js_file",
                   "retrieving_tree"),
                  "JS Syntax error prevented validation",
                  "An error in the syntax of a JavaScript file prevented "
                  "the file from being properly read by the Spidermonkey JS "
                  "engine.",
                  filename=filename)
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

    def __str__(self):
        return repr(self.value)


def _get_tree(name, code, shell=SPIDERMONKEY_INSTALLATION):
   
    # TODO : It seems appropriate to cut the `name` parameter out if the
    # parser is going to be installed locally.
    
    if not code:
        return None

    try:
        code = unicode(code)
        data = json.dumps(code)
    except UnicodeDecodeError:
        # If it's not an easily decodeable encoding, detect it and decode that
        encoding = chardet.detect(code)["encoding"].lower()
        data = json.dumps(code, encoding=encoding)

    data = """try{
        print(JSON.stringify(Reflect.parse(%s)));
    } catch(e) {
        print('{"error":true}');
    }""" % data

    # Push the data to a temporary file
    temp = tempfile.NamedTemporaryFile(mode="w+")
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
    parsed = json.loads(data)

    if "error" in parsed and parsed["error"]:
        raise JSReflectException("Reflection exception")

    return parsed

