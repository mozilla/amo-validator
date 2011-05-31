import sys
import os

import zipfile
from zipfile import ZipFile
from StringIO import StringIO

source = sys.argv[1]
target = sys.argv[2]

if not target.endswith("/"):
    target = "%s/" % target

def _unbundle(path, target):
    zf = ZipFile(path, 'r')
    contents = zf.namelist()
    for item in contents:
        sp = item.split("/")
        if not sp[-1]:
            continue

        print item, ">", target + item

        cpath = target + "/".join(sp[:-1])
        if not os.path.exists(cpath):
            os.makedirs(cpath)
        if item.endswith((".jar", ".xpi", ".zip")):
            now = target + item
            path_item = item.split("/")
            path_item[-1] = "_" + path_item[-1]
            path = target + "/".join(path_item)

            buff = StringIO(zf.read(item))
            _unbundle(buff, path + "/")
        else:
            f = open(target + item, 'w')
            f.write(zf.read(item))
            f.close()
    zf.close()

if not os.path.exists(target):
    os.mkdir(target)

_unbundle(source, target)
