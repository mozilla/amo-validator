import hashlib
import os
import sys

hash = hashlib.sha256(open(sys.argv[1]).read()).hexdigest()
print sys.argv[1], sys.argv[2], hash
