import sys
import os

import zipfile
from zipfile import ZipFile
from StringIO import StringIO

source = sys.argv[1]
target = sys.argv[2]
zf = ZipFile(target, 'w')

def _build_directory(source, zip, root):
    for item in os.listdir(source):

        if item in ("__MACOSX",
                    ".DS_Store"):
            continue

        if item.startswith("__"):
            continue

        item = "%s/%s" % (source, item)
        print item

        if os.path.isdir(item):
            if item.startswith("_") and item.endswith(".jar"):
                zipbuffer = StringIO()
                subzip = ZipFile(zipbuffer, "w")
                _build_directory(item, subzip, item)
                subzip.close()

                zip.writestr(item[len(root) + 2:], zipbuffer.getvalue())
            else:
                _build_directory(item, zip, root)
        else:
            print item[len(root) + 1:]
            zip.write(item, item[len(root) + 1:])



_build_directory(source, zf, source)
zf.close()
