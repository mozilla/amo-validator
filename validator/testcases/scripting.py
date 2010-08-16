import json

from validator.constants import *

def test_js_file(err, name, data):
    "Tests a JS file by parsing and analyzing its tokens"
    
    print data
    #print _get_tree(name, data)
    

def _get_tree(name, code):
    
    f = open("testfiles/js_ast/%s" % name)
    data = f.read()
    f.close()
    tree = json.loads(data)
    return tree
