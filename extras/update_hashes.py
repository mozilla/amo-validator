import glob
import os
import subprocess

path = os.path.dirname(__file__)
target = "jslibs"

subprocess.check_call(["python", os.path.join(path, "jslibfetcher.py"), target])
subprocess.check_call(["python", os.path.join(path, "build_hashes.py"), target])

for file in glob.glob(os.path.join(path, target, "hashes-*.txt")):
    os.rename(file, os.path.join(path, os.path.pardir, "validator", "testcases", os.path.basename(file)))

print "\nThird party library hashes updated."
