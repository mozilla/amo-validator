import json
import os
import re
import subprocess
import tempfile
from cStringIO import StringIO

import validator.testcases.javascript.traverser as traverser
from validator.testcases.javascript.spidermonkey import get_tree, \
                                                        JSReflectException
from validator.constants import SPIDERMONKEY_INSTALLATION
from validator.contextgenerator import ContextGenerator
from validator.textfilter import *

JS_ESCAPE = re.compile("\\\\+[ux]", re.I)


def test_js_file(err, filename, data, line=0):
    "Tests a JS file by parsing and analyzing its tokens"

    if SPIDERMONKEY_INSTALLATION is None or \
       err.get_resource("SPIDERMONKEY") is None:  # Default value is False
        return

    before_tier = None
    # Set the tier to 4 (Security Tests)
    if err is not None:
        before_tier = err.tier
        err.set_tier(3)

    tree = get_tree(data,
                    filename=filename,
                    shell=(err and err.get_resource("SPIDERMONKEY")) or
                          SPIDERMONKEY_INSTALLATION,
                    err=err)
    if not tree:
        if before_tier:
            err.set_tier(before_tier)
        return

    context = ContextGenerator(data)
    if traverser.DEBUG:
        _do_test(err=err, filename=filename, line=line, context=context,
                 tree=tree)
    else:
        try:
            _do_test(err=err, filename=filename, line=line, context=context,
                     tree=tree)
        except:  # pragma: no cover
            # We do this because the validator can still be damn unstable.
            # FIXME: This really needs to report an error so we know
            # that something has failed and we may not be reporting
            # important errors
            import sys, traceback
            traceback.print_exc(file=sys.stderr)
            pass

    _regex_tests(err, data, filename)

    # Reset the tier so we don't break the world
    if err is not None:
        err.set_tier(before_tier)


def test_js_snippet(err, data, filename, line=0):
    "Process a JS snippet by passing it through to the file tester."

    # Wrap snippets in a function to prevent the parser from freaking out
    # when return statements exist without a corresponding function.
    data = "(function(){%s\n})()" % data

    test_js_file(err, filename, data, line)


def _do_test(err, filename, line, context, tree):
    t = traverser.Traverser(err, filename, line, context=context)
    t.run(tree)


def _regex_tests(err, data, filename):

    c = ContextGenerator(data)

    np_warning = "Network preferences may not be modified."

    errors = {"globalStorage\\[.*\\].password":
                  "Global Storage may not be used to store passwords.",
              "network\\.http": np_warning,
              "extensions\\.blocklist\\.url": np_warning,
              "extensions\\.blocklist\\.level": np_warning,
              "extensions\\.blocklist\\.interval": np_warning,
              "general\\.useragent": np_warning,
              "launch\\(\\)":
                  "Use of 'launch()' is disallowed because of restrictions on "
                  "nsILocalFile. If the code does not use nsILocalFile, "
                  "consider a different function name.",
              "capability\\.policy":
                  "The preference 'capability.policy' is potentially unsafe."}

    for regex, message in errors.items():
        reg = re.compile(regex)
        match = reg.search(data)

        if match:
            line = c.get_line(match.start())
            err.warning(("testcases_scripting",
                         "regex_tests",
                         "compiled_error"),
                        "Potentially malicious JS",
                        message,
                        filename=filename,
                        line=line,
                        context=c)

    # JS category hunting; bug 635423

    # Generate regexes for all of them. Note that they all begin with
    # "JavaScript". Capitalization matters, bro.
    category_regexes = (
            map(re.compile,
                map(lambda r: '''"%s"|'%s'|%s''' % (r, r, r.replace(' ', '-')),
                    map(lambda r: "%s%s" % ("JavaScript ", r),
                        ("global constructor",
                         "global constructor prototype alias",
                         "global property",
                         "global privileged property",
                         "global static nameset",
                         "global dynamic nameset",
                         "DOM class",
                         "DOM interface")))))

    for cat_regex in category_regexes:
        match = cat_regex.search(data)

        if match:
            line = c.get_line(match.start())
            err.warning(("testcases_scripting",
                         "regex_tests",
                         "category_regex_tests"),
                        "Potential JavaScript category registration",
                        "Add-ons should not register JavaScript categories. "
                        "It appears that a JavaScript category was registered "
                        "via a script to attach properties to JavaScript "
                        "globals. This is not allowed.",
                        filename=filename,
                        line=line,
                        context=c)

    # DOM mutation events; bug 642153

    dom_mutation_regexes = map(
        re.compile,
        ("DOMAttrModified", "DOMAttributeNameChanged",
         "DOMCharacterDataModified", "DOMElementNameChanged",
         "DOMNodeInserted", "DOMNodeInsertedIntoDocument", "DOMNodeRemoved",
         "DOMNodeRemovedFromDocument", "DOMSubtreeModified"))

    for dom_regex in dom_mutation_regexes:
        match = dom_regex.search(data)

        if match:
            line = c.get_line(match.start())
            err.warning(
                err_id=("testcases_scripting", "regex_tests",
                        "dom_manipulation"),
                warning="DOM Mutation Events Prohibited",
                description="DOM mutation events are flagged because of their "
                            "deprecated status, as well as their extreme "
                            "inefficiency. Consider using a different event.",
                filename=filename,
                line=line,
                context=c)

