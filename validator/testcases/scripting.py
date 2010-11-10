import json
import os
import subprocess
import tempfile

import validator.testcases.javascript.traverser as traverser
from validator.contextgenerator import ContextGenerator
from validator.constants import SPIDERMONKEY_INSTALLATION as SPIDERMONKEY

def test_js_file(err, name, data, filename=None, line=0):
    "Tests a JS file by parsing and analyzing its tokens"
    
    if SPIDERMONKEY is None:
        return

    if filename is None:
        filename = name
    
    tree = _get_tree(name, data)
    
    if tree is None:
        return

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

    shell = subprocess.Popen([SPIDERMONKEY, "-f", temp.name],
	                     shell=False,
			     stderr=subprocess.PIPE,
			     stdout=subprocess.PIPE)
    results = shell.communicate()
    data = results[0]

    # Closing the temp file will delete it.
    temp.close()
    parsed = json.loads(data)
    return parsed

