import sys
import os
import hashlib

libs_folder_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), sys.argv[1])
for entry in os.listdir(libs_folder_root):
    entry_path = os.path.join(libs_folder_root, entry)
    if os.path.isdir(entry_path):
        with open(os.path.join(libs_folder_root, "hashes-{}.txt".format(entry)),
                  mode="w") as output:
            for filename in os.listdir(entry_path):
                path = os.path.join(entry_path, filename)
                hash = hashlib.sha256(open(path).read()).hexdigest()
                print path, hash
                output.write('{} {}\n'.format(hash, os.path.basename(path)))
