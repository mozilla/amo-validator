import json
import os
import subprocess

import validator.testcases.javascript.traverser as traverser
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

    t = traverser.Traverser(err, filename, line)
    t.run(tree)

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
    

def _get_tree(name, code):
   
    # TODO : It seems appropriate to cut the `name` parameter out if the
    # parser is going to be installed locally.
    
    if not code:
	return None

    data = json.dumps(code)
    data = "JSON.stringify(Reflect.parse(%s))" % data
    data = "print(%s)" % data

    temp = open("/tmp/temp.js", "w")
    temp.write(data)
    temp.close()
    
    shell = subprocess.Popen([SPIDERMONKEY, "-f", "/tmp/temp.js"],
	                     shell=False,
			     stderr=subprocess.PIPE,
			     stdout=subprocess.PIPE)
    results = shell.communicate()
    data = results[0]
    if len(data) < 5:
	print results[1]
    parsed = json.loads(data)
    return parsed

