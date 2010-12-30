import sys
import os
import os.path as pth
import hashlib

output = open("whitelist_hashes.txt", mode="w")

for root, dirs, files in os.walk(sys.argv[1]):
    for filename in files:
        path = pth.join(pth.dirname(pth.abspath(sys.argv[0])),
                        root, filename)
        hash = hashlib.sha1(open(path).read()).hexdigest()
        print path, hash
        output.write(hash + "\n")

output.close()

