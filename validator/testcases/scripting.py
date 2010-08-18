import hashlib
import json
import os

from validator.constants import *

def test_js_file(err, name, data, filename=None, line=0):
    "Tests a JS file by parsing and analyzing its tokens"
    
    if filename is None:
        filename = name
    
    tree = _get_tree(name, data)
    if tree is None:
        err.info(("testcases_scripting",
                  "test_js_file",
                  "ast_conversion_driver"),
                 "Unconverted JS",
                 ["""A JS file was found that has not been parsed into an AST
                  tree. In order to properly validate this file, a copy of the
                  code needs to be uploaded to khan.mozilla.org to
                  /home/mbasta/stage/ and "cd /home/mbasta/ & python makejs.py"
                  needs to be run. All files from /home/mbasta/output/ should
                  be copied to the testfiles/js_ast/ directory.""",
                  "Source location: testcases/js/%s" %
                      name.replace("/", "_")],
                 name)
    

def test_js_snippet(err, data, filename=None, line=0):
    
    name = hashlib.sha1(data).hexdigest()
    if filename is not None:
        name = "%s:%s" % (filename, name)
    
    test_js_file(err, name, data, filename, line)
    

def _get_tree(name, code):
    
    name = name.replace("/", "_")
    ast_name = "testfiles/js_ast/%s" % name
    
    if not os.path.exists(ast_name):
        js_name = "testfiles/js/%s" % name
        if not os.path.exists(ast_name):
            f = open(js_name, 'w')
            f.write(code)
            f.close()
        return None
    
    f = open(ast_name)
    data = f.read()
    f.close()
    tree = json.loads(data)
    return tree
