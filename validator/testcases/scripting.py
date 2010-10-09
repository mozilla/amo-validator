import json
import os

import validator.testcases.javascript.traverser as traverser
from validator.constants import SPIDERMONKEY_INSTALLATION as SPIDERMONKEY

def test_js_file(err, name, data, filename=None, line=0):
    "Tests a JS file by parsing and analyzing its tokens"
    
    if filename is None:
        filename = name
    
    tree = _get_tree(name, data)
    
    t = traverser.Traverser(err, filename, line)
    t.run(tree)

def test_js_snippet(err, data, filename=None, line=0):
    
    name = hashlib.sha1(data).hexdigest()
    if filename is not None:
        name = "%s:%s" % (filename, name)
    
    test_js_file(err, name, data, filename, line)
    

def _get_tree(name, code):
   
    # TODO : It seems appropriate to cut the `name` parameter out if the
    # parser is going to be installed locally.
    
    data = json.dumps(code);
    data = 'JSON.stringify(Reflect.parse(%s))"' % data
    data = "print(%s)" % data

    temp = open("/tmp/temp.js", "w")
    temp.write(data)
    temp.close()

    shell = os.popen("%s /tmp/temp.js >> /tmp/output.js")
    
    output = open("/tmp/output.js", "r")
    data = output.read()
    output.close()
    
    return data

