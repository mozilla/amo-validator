import json
import os
import re
import subprocess
import tempfile

import validator.testcases.javascript.traverser as traverser
from validator.contextgenerator import ContextGenerator
import validator.submain as submain
SPIDERMONKEY = submain.constants.SPIDERMONKEY_INSTALLATION

def test_js_file(err, name, data, filename=None, line=0):
    "Tests a JS file by parsing and analyzing its tokens"
    
    if SPIDERMONKEY is None:
        return

    # The filename is 
    if filename is None:
        filename = name
    
    # Get the AST tree for the JS code
    tree = _get_tree(name, data)
    if tree is None:
        return None
    
    # Set the tier to 4 (Security Tests)
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
            print "An error was encountered while attempting to validate a script"

    _regex_tests(err, data, filename)

    # Reset the tier so we don't break the world
    err.tier = before_tier

def test_js_snippet(err, data, filename=None, line=0):
    "Process a JS snippet by passing it through to the file tester."
    
    if SPIDERMONKEY is None:
        return
    
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


def _get_tree(name, code):
   
    # TODO : It seems appropriate to cut the `name` parameter out if the
    # parser is going to be installed locally.
    
    if not code:
        return None

    data = json.dumps(code)
    data = "JSON.stringify(Reflect.parse(%s))" % data
    data = "print(%s)" % data

    # Push the data to a temporary file
    temp = tempfile.NamedTemporaryFile(mode="w+")
    temp.write(data)
    temp.flush() # This is very important

    cmd = [SPIDERMONKEY, "-f", temp.name]
    shell = subprocess.Popen(cmd,
	                     shell=False,
			     stderr=subprocess.PIPE,
			     stdout=subprocess.PIPE)
    data, stderr = shell.communicate()
    if stderr:
        raise RuntimeError('Error calling %r: %s', (cmd, stderr))

    # Closing the temp file will delete it.
    temp.close()
    parsed = json.loads(data)
    return parsed

