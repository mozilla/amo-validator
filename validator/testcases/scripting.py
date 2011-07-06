import json
import os
import re
import subprocess
import tempfile
from cStringIO import StringIO

import validator.testcases.javascript.traverser as traverser
from validator.testcases.javascript.spidermonkey import get_tree, \
                                                        JSReflectException
from validator.constants import PACKAGE_THEME, SPIDERMONKEY_INSTALLATION
from validator.contextgenerator import ContextGenerator
from validator.decorator import versions_after
from validator.textfilter import *


JS_ESCAPE = re.compile("\\\\+[ux]", re.I)
NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."


def test_js_file(err, filename, data, line=0):
    "Tests a JS file by parsing and analyzing its tokens"

    if SPIDERMONKEY_INSTALLATION is None or \
       err.get_resource("SPIDERMONKEY") is None:  # Default value is False
        return

    if err.detected_type == PACKAGE_THEME:
        err.warning(
                err_id=("testcases_scripting",
                        "test_js_file",
                        "theme_js"),
                warning="JS run from theme",
                description="Themes should not contain executable code.",
                filename=filename,
                line=line)

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
                 tree=tree, data=data)
    else:
        try:
            _do_test(err=err, filename=filename, line=line, context=context,
                     tree=tree, data=data)
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

    if not data:
        return

    # Wrap snippets in a function to prevent the parser from freaking out
    # when return statements exist without a corresponding function.
    data = "(function(){%s\n})()" % data

    test_js_file(err, filename, data, line)


def _do_test(err, filename, line, context, tree, data):
    t = traverser.Traverser(err, filename, line, context=context,
                            is_jsm=(filename.endswith(".jsm") or
                                    "EXPORTED_SYMBOLS" in data))
    t.run(tree)


def _regex_tests(err, data, filename):

    c = ContextGenerator(data)

    errors = {r"globalStorage\[.*\].password":
                  "Global Storage may not be used to store passwords.",
              r"browser\.preferences\.instantApply":
                  "Changing the value of instantApply can lead to UI problems "
                  "in the browser.",
              r"network\.http": NP_WARNING,
              r"extensions(\..*)?\.update\.url": EUP_WARNING,
              r"extensions(\..*)?\.update\.enabled": EUP_WARNING,
              r"extensions(\..*)?\.update\.interval": EUP_WARNING,
              r"extensions\.blocklist\.url": NP_WARNING,
              r"extensions\.blocklist\.level": NP_WARNING,
              r"extensions\.blocklist\.interval": NP_WARNING,
              r"extensions\.blocklist\.enabled": NP_WARNING,
              r"general\.useragent": NP_WARNING,
              r"launch\(\)":
                  "Use of 'launch()' is disallowed because of restrictions on "
                  "nsILocalFile. If the code does not use nsILocalFile, "
                  "consider a different function name.",
              r"capability\.policy":
                  "The preference 'capability.policy' is potentially unsafe.",
              r"network\.websocket\.":
                  "Websocket preferences should not be modified."}

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

    # Compatibility regexes; bug 654300

    navigator_language = re.compile("navigator\\.language").search(data)
    if navigator_language:
        line = c.get_line(navigator_language.start())

        compat_references = err.get_resource("compat_references") or {}
        if "navigator_language" not in compat_references:
            compat_references["navigator_language"] = []
        compat_references["navigator_language"].append((filename, line, c))
        err.save_resource("compat_references", compat_references)


    bugzilla = "https://bugzilla.mozilla.org/show_bug.cgi?id=%d"

    interfaces = {"nsIDOMDocumentTraversal": 655514,
                  "nsIDOMDocumentRange": 655513,
                  "IWeaveCrypto": 651596}
    for interface in interfaces:
        pattern = re.compile(interface)
        match = pattern.search(data)
        if match:
            line = c.get_line(match.start())

            err.notice(
                err_id=("testcases_scripting",
                        "_regex_tests",
                        "banned_interface"),
                notice="Unsupported interface in use",
                description="Your add-on uses interface %s, which has been "
                            "removed from Firefox 6. Please refer to %s "
                            "for possible alternatives." % (
                                interface, bugzilla % interfaces[interface]),
                filename=filename,
                line=line,
                context=c,
                compatibility_type="error",
                for_appversions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                                     versions_after("firefox", "6.0a1")},
                tier=5)

    appupdatetimer = re.compile("app\\.update\\.timer")
    aut_match = appupdatetimer.search(data)
    if aut_match:
        line = c.get_line(aut_match.start())

        err.notice(
            err_id=("testcases_scripting",
                    "_regex_tests",
                    "app.update.timer"),
            notice="app.update.timer is incompatible with Firefox 6",
            description="The 'app.update.timer' preferences is being replaced "
                        "by the 'app.update.timerMinimumDelay' in Firefox 6. "
                        "Please refer to %s for more information." % (
                            bugzilla % 614181),
            filename=filename,
            line=line,
            context=c,
            compatibility_type="error",
            for_appversions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                                 versions_after("firefox", "6.0a1")})

    js_data_urls = re.compile("\\b(javascript|data):")
    jsdu_match = js_data_urls.search(data)
    if jsdu_match:
        line = c.get_line(jsdu_match.start())

        err.notice(
            err_id=("testcases_scripting",
                    "_regex_tests",
                    "javascript_data_urls"),
            notice="javascript:/data: URIs may be incompatible with Firefox 6",
            description="Loading 'javascript:' and 'data:' URIs through the "
                        " location bar may no longer work as expected in "
                        "Firefox 6. If you load these types of URIs, please "
                        "test your add-on on the latest Firefox 6 builds, or "
                        "refer to %s for more information." % (
                            bugzilla % 656433),
            filename=filename,
            line=line,
            context=c,
            compatibility_type="warning",
            for_appversions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                                 versions_after("firefox", "6.0a1")})

