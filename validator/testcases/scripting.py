from pynarcissus import jsparser

from validator.constants import *

def test_js_file(err, name, data):
    "Tests a JS file by parsing and analyzing its tokens"
    
    print data
    tree = jsparser.parse(data)
    #print str(tree)