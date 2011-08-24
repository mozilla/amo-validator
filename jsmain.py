#!/usr/bin/env python

import sys
import os

from validator.errorbundler import ErrorBundle
from validator.outputhandlers.shellcolors import OutputHandler
import validator.testcases.scripting as scripting
import validator.testcases.javascript.traverser
from validator.testcases.javascript.predefinedentities import GLOBAL_ENTITIES
import validator.testcases.javascript.spidermonkey as spidermonkey
validator.testcases.javascript.traverser.DEBUG = True

if __name__ == '__main__':
    err = ErrorBundle(instant=True)
    err.handler = OutputHandler(sys.stdout, False)
    err.supported_versions = {}
    if len(sys.argv) > 1:
        path = sys.argv[1]
        script = open(path).read()
        scripting.test_js_file(err=err,
                               filename=path,
                               data=script)
    else:
        trav = validator.testcases.javascript.traverser.Traverser(err, "stdin")
        trav._push_context()

        def do_inspect(wrapper, arguments, traverser):
            print "~" * 50
            for arg in arguments:
                if arg["type"] == "Identifier":
                    print 'Identifier: "%s"' % arg["name"]
                else:
                    print arg["type"]

                a = traverser._traverse_node(arg)
                print a.output()

                if a.is_global:
                    print a.value
                print "Context: %s" % a.context
                print "<"
            print "~" * 50

        def do_exit(wrapper, arguments, traverser):
            print "Goodbye!"
            sys.exit()

        GLOBAL_ENTITIES[u"inspect"] = {"return": do_inspect}
        GLOBAL_ENTITIES[u"exit"] = {"return": do_exit}

        while True:
            line = sys.stdin.readline()

            if line == "enable bootstrap\n":
                err.save_resource("em:bootstrap", True)
                continue
            elif line == "disable bootstrap\n":
                err.save_resource("em:bootstrap", False)
                continue
            elif line.startswith(("inspect ", "isglobal ")):
                actions = {"inspect": lambda wrap: wrap.value if
                                                    wrap.is_global else
                                                    wrap.output(),
                           "isglobal": lambda wrap: wrap.is_global}
                vars = line.split()
                final_context = trav.contexts[-1]
                for var in vars[1:]:
                    if var not in final_context.data:
                        print "%s not found." % var
                        continue
                    wrap = final_context.data[var]
                    print actions[vars[0]](wrap)
                continue

            tree = spidermonkey.get_tree(line, err)
            if tree is None:
                continue
            tree = tree["body"]
            for branch in tree:
                output = trav._traverse_node(branch)
                if output is not None:
                    print output.output()

