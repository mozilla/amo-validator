import sys
import os

import validator.testcases.scripting
from validator.testcases.javascript.traverser import MockBundler
import validator.testcases.javascript.traverser
validator.testcases.javascript.traverser.DEBUG = True

path = sys.argv[1]
script = open(path).read()
err = MockBundler()
validator.testcases.scripting.test_js_file(err,
                                           path,
                                           script)
