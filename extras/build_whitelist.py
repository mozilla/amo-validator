import sys
import os
import os.path as pth
import hashlib

with open("whitelist_hashes.txt", mode="w") as output:
    for root, dirs, files in os.walk(sys.argv[1]):
        for filename in files:
            path = pth.join(pth.dirname(pth.abspath(sys.argv[0])),
                            root, filename)
            hash = hashlib.sha256(open(path).read()).hexdigest()
            print path, hash
            output.write('%s %s\n' % (hash, pth.split(path)[-1]))

