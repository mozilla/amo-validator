import sys
import os

import zipfile
from zipfile import ZipFile
from StringIO import StringIO

source = sys.argv[1]

def _build_directory(source):
    for item in os.listdir(source):
        
        if item in ("__MACOSX",
                    ".DS_Store") or \
           item.endswith(".txt"):
            continue
        
        item = "%s/%s" % (source, item)
        print item
        
        java = os.popen("java org.mozilla.javascript.tools.shell.Main ~/Downloads/einars-js-beautify-78b3bf3/beautify.js %s" % item)
        out = open(item + ".txt", 'w')
        result = java.read()
        out.write(result)
        out.close()
        

_build_directory(source)