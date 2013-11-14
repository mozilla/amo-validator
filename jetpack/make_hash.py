import os
import sys

try:
    data = open(sys.argv[1]).read()
except:
    sys.exit(1)
else:
    if not data.strip():
        sys.exit(1)

    import hashlib
    hash = hashlib.sha256(data).hexdigest()
    print sys.argv[1], sys.argv[2], hash
