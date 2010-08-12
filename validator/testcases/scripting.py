import subprocess
from subprocess import Popen

from validator.constants import *

def test_js_file(err, name, data):
    "Tests a JS file by parsing and analyzing its tokens"
    
    print data
    print _get_tree(data)


def _get_tree(code):
    pipe = Popen(["/usr/bin/ssh",
                  "mbasta@khan.mozilla.org"],
                 stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE)
    
    pipe_out = pipe.stdin
    pipe_in = pipe.stdout
    
    print pipe.communicate(
        "cd ../clouserw/temp/spidermonkey/js/src/Linux_DBG.OBJ/\n")
    
    print pipe.communicate("./js\n")
    
    js = code.replace("\n", "\\n")
    js = js.replace("\r", "\\r")
    js = js.replace('"', '\\"')
    
    print pipe.communicate('Reflect.parse("%s");' % js)
    
    pipe.terminate()
