import sys
import os

import validator.testcases.scripting as scripting
from validator.testcases.javascript.traverser import MockBundler
import validator.testcases.javascript.traverser
import validator.testcases.javascript.spidermonkey as spidermonkey
validator.testcases.javascript.traverser.DEBUG = True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
        script = open(path).read()
        err = MockBundler()
        scripting.test_js_file(err=err,
                               filename=path,
                               data=script)
    else:
        err = MockBundler()
        trav = validator.testcases.javascript.traverser.Traverser(err, "stdin")
        trav._push_context()
        while True:
            line = sys.stdin.readline()
            tree = spidermonkey.get_tree(line, err)
            if tree is None:
                continue
            tree = tree["body"]
            for branch in tree:
                output = trav._traverse_node(branch)
                if output is not None:
                    print output.output()

