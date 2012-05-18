import re

from validator.constants import BUGZILLA_BUG
from validator.compat import (FX4_DEFINITION, FX5_DEFINITION, FX6_DEFINITION,
                              FX7_DEFINITION, FX8_DEFINITION, FX9_DEFINITION,
                              FX11_DEFINITION, FX12_DEFINITION, FX13_DEFINITION,
                              TB7_DEFINITION, TB10_DEFINITION, TB11_DEFINITION,
                              TB12_DEFINITION)
from validator.contextgenerator import ContextGenerator


registered_regex_tests = []


NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."
NSINHS_LINK = ("https://developer.mozilla.org/en/XPCOM_Interface_Reference"
               "/nsINavHistoryService")
TB7_LINK = "https://developer.mozilla.org/en/Thunderbird_7_for_developers"

GENERIC_PATTERNS = {
    r"globalStorage\[.*\].password":
        "Global Storage may not be used to store passwords.",
    r"launch\(\)":
        "Use of 'launch()' is disallowed because of restrictions on "
        "nsILocalFile. If the code does not use nsILocalFile, consider a "
        "different function name."}

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
PROTOTYPE_REGEX = re.compile(r"(String|Object|Number|Date|RegExp|Function|"
                             r"Boolean|Array|Iterator)\.prototype"
                             r"(\.[a-zA-Z0-9]+|\[.+\]) =", re.I)

CHROME_PATTERNS = (
    (r"(?<![\'\"])require\s*\(\s*[\'\"]"
     r"(chrome|window-utils|observer-service)"
     r"[\'\"]\s*\)",
        'Usage of non-SDK interface',
        "This SDK-based add-on uses interfaces that aren't part of the SDK."),
)


# DOM mutation events; bug 642153
DOM_MUTATION_REGEXES = map(re.compile,
        ("DOMAttrModified", "DOMAttributeNameChanged",
         "DOMCharacterDataModified", "DOMElementNameChanged",
         "DOMNodeInserted", "DOMNodeInsertedIntoDocument", "DOMNodeRemoved",
         "DOMNodeRemovedFromDocument", "DOMSubtreeModified"))

TB11_STRINGS = {"newToolbarCmd\.(label|tooltip)": 694027,
                "openToolbarCmd\.(label|tooltip)": 694027,
                "saveToolbarCmd\.(label|tooltip)": 694027,
                "publishToolbarCmd\.(label|tooltip)": 694027,
                "messengerWindow\.title": 701671,
                "folderContextSearchMessages\.(label|accesskey)": 652555,
                "importFromSeamonkey2\.(label|accesskey)": 689437,
                "comm4xMailImportMsgs\.properties": 689437,
                "specialFolderDeletionErr": 39121,
                "sourceNameSeamonkey": 689437,
                "sourceNameOExpress": 689437,
                "sourceNameOutlook": 689437,
                "failedDuplicateAccount": 709020,}

TB12_STRINGS = {"editImageMapButton\.(label|tooltip)": 717240,
                "haveSmtp[1-3]\.suffix2": 346306,
                "EditorImage(Map|MapHotSpot)\.dtd": 717240,
                "subscribe-errorInvalidOPMLFile": 307629,}

TB11_JS = {"onViewToolbarCommand": 644169,
           "nsContextMenu": 680192,
           "MailMigrator\.migrateMail": 712395,
           "AddUrlAttachment": 708982,
           "makeFeedObject": 705504,
           "deleteFeed": 705504,}

TB12_JS = {"TextEditorOnLoad": 695842,
           "Editor(OnLoad|Startup|Shutdown|CanClose)": 695842,
           "gInsertNewIMap": 717240,
           "editImageMap": 717240,
           "(SelectAll|MessageHas)Attachments": 526998,}

def run_regex_tests(document, err, filename, context=None, is_js=False):
    """Run all of the regex-based JS tests."""

    if context is None:
        context = ContextGenerator(document)

    def _generic_test(pattern, title, message, metadata={}):
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
            if metadata:
                err.metadata.update(metadata)

    def _substring_test(pattern, title, message):
        """Run a single substringest."""
        match = re.compile(pattern).search(document)
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

    def _compat_test(pattern, title, message, compatibility_type,
                     appversions=None, logFunc=err.notice):
        """Run a single regex test and return a compatibility message."""
        match = pattern.search(document)
        if match:
            line = context.get_line(match.start())
            logFunc(
                ("testcases_javascript_regex", "generic", "_compat_test"),
                title,
                description=message,
                filename=filename,
                line=line,
                context=context,
                compatibility_type=compatibility_type,
                for_appversions=appversions,
                tier=5)

    if not filename.startswith("defaults/preferences/"):
        from javascript.predefinedentities import (BANNED_PREF_BRANCHES,
                                                   BANNED_PREF_REGEXPS)
        for pattern in BANNED_PREF_REGEXPS:
            _generic_test(
                re.compile("[\"']" + pattern),
                "Potentially unsafe preference branch referenced",
                "Extensions should not alter preferences matching /%s/"
                    % pattern)

        for branch in BANNED_PREF_BRANCHES:
            _substring_test(
                branch.replace(r".", r"\."),
                "Potentially unsafe preference branch referenced",
                "Extensions should not alter preferences in the '%s' "
                "preference branch" % branch)

    for pattern, message in GENERIC_PATTERNS.items():
        _generic_test(
                re.compile(pattern),
                "Potentially unsafe JS in use.",
                message)

    for pattern, title, message in CHROME_PATTERNS:
        _generic_test(re.compile(pattern), title, message,
                      {'requires_chrome': True})

    if is_js:
        for pattern in CATEGORY_REGEXES:
            _generic_test(
                    pattern,
                    "Potential JavaScript category registration",
                    "Add-ons should not register JavaScript categories. It "
                    "appears that a JavaScript category was registered via a "
                    "script to attach properties to JavaScript globals. This "
                    "is not allowed.")

        if re.match(r"defaults/preferences/.+\.js", filename):
            _generic_test(
                PASSWORD_REGEX,
                "Passwords may be stored in /defaults/preferences JS files.",
                "Storing passwords in the preferences is insecure and the "
                "Login Manager should be used instead.")

        is_jsm = filename.endswith(".jsm") or "EXPORTED_SYMBOLS" in document

        if not is_jsm:
            # Have a non-static/dynamic test for prototype extension.
            _generic_test(
                    PROTOTYPE_REGEX,
                    "JS Prototype extension",
                    "It appears that an extension of a built-in JS type was "
                    "made. This is not allowed for security and compatibility "
                    "reasons.")

    for pattern in DOM_MUTATION_REGEXES:
        _generic_test(
                pattern,
                "DOM Mutation Events Prohibited",
                "DOM mutation events are flagged because of their "
                "deprecated status, as well as their extreme "
                "inefficiency. Consider using a different event.")

    # Thunderbird 7 Compatibility rdf:addressdirectory
    if err.supports_version(TB7_DEFINITION):
        # dictUtils.js removal
        _compat_test(
                re.compile(r"resource:///modules/dictUtils.js"),
                "dictUtils.js was removed in Thunderbird 7.",
                "The dictUtils.js file is no longer available in "
                "Thunderbird 7. You can use Dict.jsm instead. See"
                "%s for more information." % BUGZILLA_BUG % 621213,
                compatibility_type="error",
                appversions=TB7_DEFINITION,
                logFunc=err.warning)
        # de-RDF the addressbook
        _compat_test(
                re.compile(r"rdf:addressdirectory"),
                "The address book does not use RDF in Thunderbird 7.",
                "The address book was changed to use a look up table in "
                "Thunderbird 7. See %s and %s for more information." %
                    (TB7_LINK, BUGZILLA_BUG % 621213),
                compatibility_type="error",
                appversions=TB7_DEFINITION)
        # Second test for de-RDFing the addressbook
        # r"GetResource(.*?)\s*\.\s*QueryInterface(.*?nsIAbDirectory);"
        _compat_test(
                re.compile(r"GetResource\(.*?\)\s*\.\s*"
                           r"QueryInterface\(.*?nsIAbDirectory\)"),
                "The address book does not use RDF in Thunderbird 7.",
                "The address book was changed to use a look up table in "
                "Thunderbird 7. See %s and %s for more information." %
                    (TB7_LINK, BUGZILLA_BUG % 621213),
                compatibility_type="error",
                appversions=TB7_DEFINITION)

    # Thunderbird 10 Compatibility
    if err.supports_version(TB10_DEFINITION):
        # gDownloadManagerStrings removal
        _compat_test(
                re.compile(r"gDownloadManagerStrings"),
                "gDownloadManagerStrings was removed in Thunderbird 10.",
                "This global is no longer available in "
                "Thunderbird 10. See %s for more information." %
                    BUGZILLA_BUG % 700220,
                compatibility_type="error",
                appversions=TB10_DEFINITION,
                logFunc=err.warning)
        # nsTryToClose.js removal
        _compat_test(
                re.compile(r"nsTryToClose.js"),
                "nsTryToClose.js was removed in Thunderbird 10.",
                "The nsTryToClose.js file is no longer available in "
                "Thunderbird 10. See %s for more information." %
                    BUGZILLA_BUG % 539997,
                compatibility_type="error",
                appversions=TB10_DEFINITION,
                logFunc=err.warning)

    # Thunderbird 11 Compatibility
    if err.supports_version(TB11_DEFINITION):
        # specialFoldersDeletionAllowed removal
        _compat_test(
            re.compile(r"specialFoldersDeletionAllowed"),
            "specialFoldersDeletionAllowed was removed in Thunderbird 11.",
            "This global is no longer available in "
            "Thunderbird 11. See %s for more information." %
            BUGZILLA_BUG % 39121,
            compatibility_type="error",
            appversions=TB11_DEFINITION,
            logFunc=err.notice)
        for pattern, bug in TB11_STRINGS.items():
            _compat_test(
                re.compile(pattern),
                "Removed, renamed, or changed strings in use",
                "Your add-on uses string %s, which has been changed or "
                "removed from Thunderbird 11. Please refer to %s for "
                "possible alternatives." % (pattern, BUGZILLA_BUG % bug),
                compatibility_type="error",
                appversions=TB11_DEFINITION,
                logFunc=err.warning)
        for pattern, bug in TB11_JS.items():
            _compat_test(
                re.compile(pattern),
                "Removed, renamed, or changed javascript in use",
                "Your add-on uses the javascript method or class %s, which "
                "has been changed or removed from Thunderbird 11. Please "
                "refer to %s for possible alternatives." %
                (pattern, BUGZILLA_BUG % bug),
                compatibility_type="error",
                appversions=TB11_DEFINITION,
                logFunc=err.notice)

    # Thunderbird 12 Compatibility
    if err.supports_version(TB12_DEFINITION):
        _compat_test(
            re.compile(r"EdImage(Map|MapHotSpot|MapShapes|Overlay)\.js"),
            "Removed javascript file EdImage*.js in use ",
            "EdImageMap.js, EdImageMapHotSpot.js, "
            "EdImageMapShapes.js, and EdImageMapOverlay.js "
            "were removed in Thunderbird 12. "
            "See %s for more information." % BUGZILLA_BUG % 717240,
            compatibility_type="error",
            appversions=TB12_DEFINITION,
            logFunc=err.notice)
        for pattern, bug in TB12_STRINGS.items():
            _compat_test(
                re.compile(pattern),
                "Removed, renamed, or changed strings in use",
                "Your add-on uses string %s, which has been changed or "
                "removed from Thunderbird 11. Please refer to %s for "
                "possible alternatives." % (pattern, BUGZILLA_BUG % bug),
                compatibility_type="error",
                appversions=TB12_DEFINITION,
                logFunc=err.warning)
        for pattern, bug in TB12_JS.items():
            _compat_test(
                re.compile(pattern),
                "Removed, renamed, or changed javascript in use",
                "Your add-on uses the javascript method or class %s, which "
                "has been changed or removed from Thunderbird 11. Please "
                "refer to %s for possible alternatives." %
                (pattern, BUGZILLA_BUG % bug),
                compatibility_type="error",
                appversions=TB12_DEFINITION,
                logFunc=err.notice)

    # Run all of the registered tests.
    for cls in registered_regex_tests:
        if not cls.applicable(err, filename):
            continue
        t = cls(err, document, filename, context)
        # Run standard tests.
        for test in t.tests():
            test()
        # Run tests that would otherwise be guarded by `is_js`.
        if is_js:
            for test in t.js_tests():
                test()


def register_generator(cls):
    registered_regex_tests.append(cls)
    return cls


class RegexTestGenerator(object):
    """
    This stubs out a test generator object. By decorating inheritors of this
    class with `@register_generator`, the regex tests will be run on any files
    that are passed to `run_regex_tests()`.
    """

    def __init__(self, err, document, filename, context):
        self.err = err
        self.document = document
        self.filename = filename
        self.context = context

        self.app_versions_fallback = None

    @classmethod
    def applicable(cls, err, filename):
        """Return whether the tests apply to the current file."""
        return True  # Default to always applicable.

    def tests(self):
        """Override this with a generator that produces the regex tests."""
        return []

    def js_tests(self):
        """
        Override this with a generator that produces regex tests that are
        exclusive to JavaScript.
        """
        return []

    def get_test(self, pattern, title, message, log_function=None,
                 compat_type=None, app_versions=None):
        """
        Return a function that, when called, will log a compatibility warning
        or error.
        """
        app_versions = app_versions or self.app_versions_fallback
        log_function = log_function or self.err.warning
        def wrapper():
            for match in re.finditer(pattern, self.document):
                log_function(
                        ("testcases_regex", "generic", "_generated"),
                        title,
                        message,
                        filename=self.filename,
                        line=self.context.get_line(match.start()),
                        context=self.context,
                        compatibility_type=compat_type,
                        for_appversions=app_versions,
                        tier=err.tier if app_versions is None else 5)

        return wrapper

    def get_test_bug(self, bug, pattern, title, message, **kwargs):
        """Helper function to mix in a bug number."""
        message = [message,
                   "See bug %s for more information." % BUGZILLA_BUG % bug]
        return self.get_test(pattern, title, message, **kwargs)


class CompatRegexTestHelper(RegexTestGenerator):
    """
    A helper that makes it easier to stay DRY. This will automatically check
    for applicability against the value set as the app_versions_fallback.
    """

    def __init__(self, *args, **kwargs):
        super(CompatRegexTestHelper, self).__init__(*args, **kwargs)
        self.app_versions_fallback = self.VERSION

    @classmethod
    def applicable(cls, err, filename):
        return err.supports_version(cls.VERSION)


DEP_INTERFACE = "Deprecated interface in use"
DEP_INTERFACE_DESC = ("This add-on uses `%s`, which is deprecated in Gecko %d "
                      "and should not be used.")

@register_generator
class Gecko5RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 5 updates."""

    VERSION = FX5_DEFINITION

    def tests(self):
        yield self.get_test(
                r"navigator\.language",
                "`navigator.language` may not behave as expected.",
                "JavaScript code was found that references `navigator."
                "language`, which will no longer indicate that language of "
                "the application's UI. To maintain existing functionality, "
                "`general.useragent.locale` should be used in place of "
                "`navigator.language`.", compat_type="error",
                log_function=self.err.notice)


@register_generator
class Gecko6RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 6 updates."""

    VERSION = FX6_DEFINITION

    def tests(self):
        interfaces = {"nsIDOMDocumentTraversal": 655514,
                      "nsIDOMDocumentRange": 655513,
                      "IWeaveCrypto": 651596}
        for interface, bug in interfaces.items():
            yield self.get_test_bug(
                    bug=bug,
                    pattern=interface,
                    title=DEP_INTERFACE,
                    message=DEP_INTERFACE_DESC % (interface, 6),
                    compat_type="error")

        yield self.get_test_bug(
                614181, r"app\.update\.timer",
                "`app.update.timer` is incompatible with Gecko 6",
                "The `app.update.timer` preference is being replaced by the "
                "`app.update.timerMinimumDelay` preference in Gecko 6.",
                compat_type="error")

    def js_tests(self):
        yield self.get_test_bug(
                656433, r"['\"](javascript|data):",
                "`javascript:`/`data:` URIs may be incompatible with Gecko 6",
                "Loading `javascript:` and `data:` URIs through the location "
                "bar may no longer work as expected in Gecko 6. If you load "
                "these types of URIs, please test your add-on using the "
                "latest builds of the applications that it targets.",
                compat_type="warning", log_function=self.err.notice)


@register_generator
class Gecko7RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 7 updates."""

    VERSION = FX7_DEFINITION

    def tests(self):
        interfaces = {"nsIDOMDocumentStyle": 658904,
                      "nsIDOMNSDocument": 658906,
                      "nsIDOM3TypeInfo": 660539,
                      "nsIDOM3Node": 659053}
        for interface, bug in interfaces.items():
            yield self.get_test_bug(
                    bug=bug,
                    pattern=interface,
                    title=DEP_INTERFACE,
                    message=DEP_INTERFACE_DESC % (interface, 7),
                    compat_type="error")

        yield self.get_test_bug(
                633266, "nsINavHistoryObserver",
                "`nsINavHistoryObserver` interface has changed in Gecko 7",
                "The `nsINavHistoryObserver` interface has change in Gecko 7. "
                "Most function calls now require a GUID parameter. Please "
                "refer to %s for more information." % NSINHS_LINK,
                compat_type="error", log_function=self.err.notice)
        yield self.get_test_bug(
                617539, "nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH",
                "`_MOZILLA_2_0_BRANCH` has been merged in Gecko 7",
                "The `_MOZILLA_2_0_BRANCH` interfaces have been merged out. "
                "You should now use the namespace without the "
                "`_MOZILLA_2_0_BRANCH` suffix.", compat_type="warning")


@register_generator
class Gecko8RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 8 updates."""

    VERSION = FX8_DEFINITION

    def tests(self):
        interfaces = {"nsISelection2": 672536,
                      "nsISelection3": 672536}
        for interface, bug in interfaces.items():
            yield self.get_test_bug(
                    bug=bug,
                    pattern=interface,
                    title=DEP_INTERFACE,
                    message=DEP_INTERFACE_DESC % (interface, 8),
                    compat_type="error")

        NSIDWI_MDN = ("https://developer.mozilla.org/en/"
                      "XPCOM_Interface_Reference/nsIDOMWindow")
        yield self.get_test(
                "nsIDOMWindowInternal", DEP_INTERFACE,
                "The `nsIDOMWindowInternal` interface has been deprecated in "
                "Gecko 8. You can use the `nsIDOMWindow` interface instead. "
                "See %s for more information." % NSIDWI_MDN,
                compat_type="warning")

        ISO8601_MDC = ("https://developer.mozilla.org/en/JavaScript/Reference/"
                       "Global_Objects/Date")
        yield self.get_test(
                "ISO8601DateUtils",
                "`ISO8601DateUtils.jsm` was removed in Gecko 8",
                "The `ISO8601DateUtils object is no longer available in Gecko "
                "8. You can use the normal `Date` object instead. See %s"
                "for more information." % ISO8601_MDC,
                compat_type="error")


@register_generator
class Gecko9RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 8 updates."""

    VERSION = FX9_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                679971, r"navigator\.taintEnabled",
                "`navigator.taintEnabled` was removed in Gecko 9",
                "The `taintEnabled` function is no longer available in Gecko "
                "9. Since this function was only used for browser detection "
                "and this doesn't belong in extension code, it should be "
                "removed if possible.", compat_type="warning")

        chrome_context_props = [r"\.nodePrincipal", r"\.documentURIObject",
                                r"\.baseURIObject", ]
        for property in chrome_context_props:
            yield self.get_test_bug(
                    660233, property,
                    "`%s` only available in chrome contexts" % property,
                    "The `%s` property is no longer accessible from untrusted "
                    "scripts as of Gecko 9." % property,
                    compat_type="warning", log_function=self.err.notice)

        yield self.get_test_bug(
                568971, r"nsIGlobalHistory3", DEP_INTERFACE,
                DEP_INTERFACE_DESC % ("nsIGlobalHistory3", 9),
                compat_type="warning")

        # geo.wifi.* warnings
        for pattern in ["geo.wifi.uri", r"geo.wifi.protocol", ]:
            yield self.get_test_bug(
                    689252, pattern.replace(".", r"\."),
                    "`%s` removed in Gecko 9" % pattern,
                    "The `geo.wifi.*` preferences are no longer created by "
                    "default in Gecko 9. Reading them without testing for "
                    "their presence can result in unexpected errors.",
                    compat_type="error")


@register_generator
class Gecko11RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 11 updates."""

    VERSION = FX11_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                700490, "nsICharsetResolver", DEP_INTERFACE,
                DEP_INTERFACE_DESC % ("nsICharsetResolver", 11),
                compat_type="error")

        yield self.get_test_bug(
                701875, r"omni\.jar",
                "`omni.jar` renamed to `omni.ja` in Gecko 11",
                "This add-on references `omni.jar`, which was renamed to "
                "`omni.ja`. You should avoid referencing this file directly, "
                "and at least update this reference for any versions that "
                "support Gecko 11 and above.", compat_type="error")


@register_generator
class Gecko12RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 12 updates."""

    VERSION = FX12_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                675221, "nsIProxyObjectManager", DEP_INTERFACE,
                "This add-on uses nsIProxyObjectManager, which was removed in "
                "Gecko 12.", compat_type="error")
        yield self.get_test_bug(
                713825, "documentCharsetInfo",
                "Deprecated JavaScript property",
                "documentCharsetInfo has been deprecated in Gecko 12 and "
                "should no longer be used.", compat_type="error")
        yield self.get_test_bug(
                711838, "nsIJetpack(Service)?", DEP_INTERFACE,
                "This add-on uses the Jetpack service, which was deprecated "
                "long ago and is no longer included in Gecko 12. Please "
                "update your add-on to use a more recent version of the "
                "Add-ons SDK.", compat_type="error")

        # `chromemargin`; bug 735876
        yield self.get_test_bug(
                735876, "chromemargin",
                "`chromemargin` attribute changed in Gecko 12",
                "This add-on uses the chromemargin attribute, which after "
                "Gecko 12 will not work in the same way with values other "
                "than 0 or -1.", compat_type="error",
                log_function=self.err.notice)

@register_generator
class Gecko13RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 13 updates."""

    VERSION = FX13_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                613588, "nsILivemarkService", DEP_INTERFACE,
                "This add-on uses nsILivemarkService, which has been "
                "deprecated in Gecko 13. Some of its functions may not work "
                "as expected. mozIAsyncLivemarks should be used instead.",
                compat_type="error")
        yield self.get_test_bug(
                718255, "nsIPrefBranch2", DEP_INTERFACE,
                "This add-on uses nsIPrefBranch2, which has been merged into "
                "nsIPrefBranch in Gecko 13. Once you drop support for old "
                "versions of Gecko, you should stop using nsIPrefBranch2. You "
                "can use the == operator as an alternative.",
                compat_type="warning")
        yield self.get_test_bug(
                650784, "nsIScriptableUnescapeHTML", DEP_INTERFACE,
                "This add-on uses nsIScriptableUnescapeHTML, which has been "
                "deprecated in Gecko 13 in favor of the nsIParserUtils "
                "interface. While it will continue to work for the foreseeable "
                "future, it is recommended that you change your code to use "
                "nsIParserUtils as soon as possible.",
                compat_type="warning", log_function=self.err.notice)


