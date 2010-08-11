import sys
import os

import validator.testcases.scripting

path = sys.argv[1]
script = open(path)

validator.testcases.scripting.test_js_file(None,
                                           path,
                                           script)