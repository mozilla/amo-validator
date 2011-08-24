import fnmatch
import re

from validator.constants import BUGZILLA_BUG
from validator.contextgenerator import ContextGenerator
from validator.decorator import version_range


NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."
NSINHS_LINK = ("https://developer.mozilla.org/en/XPCOM_Interface_Reference"
               "/nsINavHistoryService")

GENERIC_PATTERNS = {
    r"globalStorage\[.*\].password":
        "Global Storage may not be used to store passwords.",
    r"browser\.preferences\.instantApply":
        "Changing the value of instantApply can lead to UI problems in the "
        "browser.",
    r"network\.http": NP_WARNING,
    r"network\.websocket": "Websocket preferences should not be modified.",
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
        "nsILocalFile. If the code does not use nsILocalFile, consider a "
        "different function name.",
    r"capability\.policy":
        "The preference 'capability.policy' is potentially unsafe."}

# JS category hunting; bug 635423
# Generate regexes for all of them. Note that they all begin with
# "JavaScript". Capitalization matters, bro.
CATEGORY_REGEXES = (
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

PASSWORD_REGEX = re.compile("password", re.I)

# DOM mutation events; bug 642153
DOM_MUTATION_REGEXES = map(re.compile,
        ("DOMAttrModified", "DOMAttributeNameChanged",
         "DOMCharacterDataModified", "DOMElementNameChanged",
         "DOMNodeInserted", "DOMNodeInsertedIntoDocument", "DOMNodeRemoved",
         "DOMNodeRemovedFromDocument", "DOMSubtreeModified"))

FX6_INTERFACES = {"nsIDOMDocumentTraversal": 655514,
                  "nsIDOMDocumentRange": 655513,
                  "IWeaveCrypto": 651596}
FX7_INTERFACES = {"nsIDOMDocumentStyle": 658904,
                  "nsIDOMNSDocument": 658906,
                  "nsIDOM3TypeInfo": 660539,
                  "nsIDOM3Node": 659053}
FX8_INTERFACES = {"nsISelection2": 672536,
                  "nsISelection3": 672536}

FX4_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "3.7a1pre", "5.0a2")}
FX5_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "5.0a2", "6.0a1")}
FX6_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "6.0a1", "7.0a1")}
FX7_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "7.0a1", "8.0a1")}
FX8_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "8.0a1", "9.0a1")}


def run_regex_tests(document, err, filename, context=None, is_js=False):
    """Run all of the regex-based JS tests."""

    if context is None:
        context = ContextGenerator(document)

    def _generic_test(pattern, title, message):
        """Run a single regex test."""
        match = pattern.search(document)
        if match:
            line = context.get_line(match.start())
            err.warning(
                err_id=("testcases_javascript_regex", "generic",
                        "_generic_test"),
                warning=title,
                description=message,
                filename=filename,
                line=line,
                context=context)

    def _compat_test(pattern, title, message, compatibility_type=None,
                     appversions=None):
        """Run a single regex test and return a compatibility message."""
        match = pattern.search(document)
        if match:
            line = context.get_line(match.start())
            err.notice(
                err_id=("testcases_javascript_regex", "generic",
                        "_compat_test"),
                notice=title,
                description=message,
                filename=filename,
                line=line,
                context=context,
                compatibility_type=compatibility_type,
                for_appversions=appversions,
                tier=5)

    for pattern, message in GENERIC_PATTERNS.items():
        _generic_test(
                re.compile(pattern),
                "Potentially unsafe JS in use.",
                message)

    if is_js:
        for pattern in CATEGORY_REGEXES:
            _generic_test(
                    pattern,
                    "Potential JavaScript category registration",
                    "Add-ons should not register JavaScript categories. It "
                    "appears that a JavaScript category was registered via a "
                    "script to attach properties to JavaScript globals. This "
                    "is not allowed.")

        if fnmatch.fnmatch(filename, "defaults/preferences/*.js"):
            _generic_test(
                PASSWORD_REGEX,
                "Passwords may be stored in /defaults/preferences JS files.",
                "Storing passwords in the preferences is insecure and the "
                "Login Manager should be used instead.")

    for pattern in DOM_MUTATION_REGEXES:
        _generic_test(
                pattern,
                "DOM Mutation Events Prohibited",
                "DOM mutation events are flagged because of their "
                "deprecated status, as well as their extreme "
                "inefficiency. Consider using a different event.")

    # Firefox 5 Compatibility
    if err.supports_version(FX5_DEFINITION):
        _compat_test(
                re.compile(r"navigator\.language"),
                "navigator.language may not behave as expected",
                ("JavaScript code was found that references "
                 "navigator.language, which will no longer indicate "
                 "the language of Firefox's UI. To maintain existing "
                 "functionality, general.useragent.locale should be "
                 "used in place of `navigator.language`."),
                compatibility_type="error",
                appversions=FX5_DEFINITION)

    # Firefox 6 Compatibility
    if err.supports_version(FX6_DEFINITION):
        for pattern, bug in FX6_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    ("Your add-on uses interface %s, which has been removed "
                     "from Firefox 6. Please refer to %s for possible "
                     "alternatives.") % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX6_DEFINITION)

        # app.update.timer
        _compat_test(
                re.compile(r"app\.update\.timer"),
                "app.update.timer is incompatible with Firefox 6",
                ("The 'app.update.timer' preference is being replaced by the "
                 "'app.update.timerMinimumDelay' preference in Firefox 6. "
                 "Please refer to %s for more details.") %
                     (BUGZILLA_BUG % 614181),
                compatibility_type="error",
                appversions=FX6_DEFINITION)
        if is_js:
            # javascript/data: URI usage in the address bar
            _compat_test(
                    re.compile(r"\b(javascript|data):"),
                    "javascript:/data: URIs may be incompatible with Firefox "
                    "6.",
                    ("Loading 'javascript:' and 'data:' URIs through the "
                     "location bar may no longer work as expected in Firefox "
                     "6. If you load these types of URIs, please test your "
                     "add-on on the latest Firefox 6 builds, or refer to %s "
                     "for more information.") %
                         (BUGZILLA_BUG % 656433),
                    compatibility_type="warning",
                    appversions=FX6_DEFINITION)

    # Firefox 7 Compatibility
    if err.supports_version(FX7_DEFINITION):
        for pattern, bug in FX7_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    ("Your add-on uses interface %s, which has been removed "
                     "from Firefox 7. Please refer to %s for possible "
                     "alternatives.") % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX7_DEFINITION)

        # nsINavHistoryObserver
        _compat_test(
                re.compile(r"nsINavHistoryObserver"),
                "nsINavHistoryObserver interface has changed in Firefox 7",
                ("The nsINavHistoryObserver interface has changed in Firefox "
                 "7. Most function calls now required a GUID parameter, "
                 "please refer to %s and %s for more information.") %
                    (NSINHS_LINK, BUGZILLA_BUG % 633266),
                compatibility_type="error",
                appversions=FX7_DEFINITION)
        # nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH
        _compat_test(
                re.compile(r"nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH"),
                "MOZILLA_2_0 Namespace has been merged in Firefox 7",
                ("The '_MOZILLA_2_0_BRANCH' interfaces have been merged out. "
                 "You should now use the namespace without the "
                 "'_MOZILLA_2_0_BRANCH' suffix. Please refer to %s for more "
                 "details.") %
                     (BUGZILLA_BUG % 617539),
                compatibility_type="warning",
                appversions=FX7_DEFINITION)

    # Firefox 8 Compatibility
    if err.supports_version(FX8_DEFINITION):
        for pattern, bug in FX8_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Removed, deprecated, or unsupported interface in use.",
                    ("The nsISelection2 and nsISelection3 interfaces have "
                     "been removed in Firefox 8. You can use the nsISelection "
                     "interface instead. See %s for more details.") %
                        (BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX8_DEFINITION)

        # nsIDOMWindowInternal
        NSIDWI_MDN = ("https://developer.mozilla.org/en/"
                          "XPCOM_Interface_Reference/nsIDOMWindow")
        _compat_test(
                re.compile(r"nsIDOMWindowInternal"),
                "nsIDOMWindowInternal has been deprecated in Firefox 8.",
                ("The nsIDOMWindowInternal interface has been deprecated in "
                 "Firefox 8. You can use the nsIDOMWindow interface instead. "
                 "See %s for more information.") % NSIDWI_MDN,
                compatibility_type="warning",
                appversions=FX8_DEFINITION)

