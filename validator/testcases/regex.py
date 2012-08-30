import re

from validator.constants import BUGZILLA_BUG
from validator.compat import (FX4_DEFINITION, FX5_DEFINITION, FX6_DEFINITION,
                              FX7_DEFINITION, FX8_DEFINITION, FX9_DEFINITION,
                              FX11_DEFINITION, FX12_DEFINITION, FX13_DEFINITION,
                              FX14_DEFINITION, FX15_DEFINITION,
                              TB7_DEFINITION, TB10_DEFINITION, TB11_DEFINITION,
                              TB12_DEFINITION, TB13_DEFINITION, TB14_DEFINITION,
                              TB15_DEFINITION)
from validator.contextgenerator import ContextGenerator


registered_regex_tests = []


NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."
NSINHS_LINK = ("https://developer.mozilla.org/en/XPCOM_Interface_Reference"
               "/nsINavHistoryService")
TB7_LINK = "https://developer.mozilla.org/en/Thunderbird_7_for_developers"


def run_regex_tests(document, err, filename, context=None, is_js=False):
    """Run all of the regex-based JS tests."""

    if context is None:
        context = ContextGenerator(document)

    # Run all of the registered tests.
    for cls in registered_regex_tests:
        if not cls.applicable(err, filename, document):
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
    def applicable(cls, err, filename, document):
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
                 compat_type=None, app_versions=None, flags=0):
        """
        Return a function that, when called, will log a compatibility warning
        or error.
        """
        app_versions = app_versions or self.app_versions_fallback
        log_function = log_function or self.err.warning
        def wrapper():
            matched = False
            for match in re.finditer(pattern, self.document, flags):
                log_function(
                        ("testcases_regex", "generic", "_generated"),
                        title,
                        message,
                        filename=self.filename,
                        line=self.context.get_line(match.start()),
                        context=self.context,
                        compatibility_type=compat_type,
                        for_appversions=app_versions,
                        tier=self.err.tier if app_versions is None else 5)
                matched = True
            return matched

        return wrapper

    def get_test_bug(self, bug, pattern, title, message, **kwargs):
        """Helper function to mix in a bug number."""
        message = [message,
                   "See bug %s for more information." % BUGZILLA_BUG % bug]
        return self.get_test(pattern, title, message, **kwargs)


@register_generator
class GenericRegexTests(RegexTestGenerator):
    """Test for generic, banned patterns in a document being scanned."""

    def tests(self):
        # globalStorage.(.+)password test removed for bug 752740

        yield self.get_test(
                r"launch\(\)",
                "`launch()` disallowed",
                "Use of `launch()` is disallowed because of restrictions on "
                "`nsIFile` and `nsILocalFile`. If the code does not use "
                "those namespaces, consider using a different function name.")

        yield self.get_test(
                r"resource://services-sync",
                "Sync services objects are not intended to be re-used",
                "The Sync services objects are not intended to be re-used, and "
                "they often change in ways that break add-ons. It is strongly "
                "recommended that you do not rely on them.")


@register_generator
class CategoryRegexTests(RegexTestGenerator):
    """
    These tests will flag JavaScript category registration. Category
    registration is not permitted in add-ons.

    Added from bug 635423
    """

    # This generates the regular expressions for all combinations of JS
    # categories. Note that all of them begin with "JavaScript". Capitalization
    # matters.
    PATTERNS = map(lambda r: '''"%s"|'%s'|%s''' % (r, r, r.replace(" ", "-")),
                   ["JavaScript %s" % pattern for pattern in
                    ("global constructor",
                     "global constructor prototype alias",
                     "global property",
                     "global privileged property",
                     "global static nameset",
                     "global dynamic nameset",
                     "DOM class",
                     "DOM interface", )])

    def js_tests(self):
        for pattern in self.PATTERNS:
            yield self.get_test(
                    pattern,
                    "Potential JavaScript category registration",
                    "Add-ons should not register JavaScript categories. It "
                    "appears that a JavaScript category was registered via a "
                    "script to attach properties to JavaScript globals. This "
                    "is not allowed.")


@register_generator
class DOMMutationRegexTests(RegexTestGenerator):
    """
    These regex tests will test that DOM mutation events are not used. These
    events have extreme performance penalties associated with them and are
    currently deprecated.

    Added from bug 642153
    """

    EVENTS = ("DOMAttrModified", "DOMAttributeNameChanged",
              "DOMCharacterDataModified", "DOMElementNameChanged",
              "DOMNodeInserted", "DOMNodeInsertedIntoDocument",
              "DOMNodeRemoved", "DOMNodeRemovedFromDocument",
              "DOMSubtreeModified", )

    def js_tests(self):
        for event in self.EVENTS:
            yield self.get_test(
                    event,
                    "DOM mutation event use prohibited",
                    "DOM mutation events are flagged because of their "
                    "deprecated status as well as their extreme inefficiency. "
                    "Consider using a different event.")


@register_generator
class PasswordsInPrefsRegexTests(RegexTestGenerator):
    """
    These regex tests will ensure that the developer is not storing passwords
    in the `/defaults/preferences` JS files.

    Added from bug 647109
    """

    @classmethod
    def applicable(cls, err, filename, document):
        return bool(re.match(r"defaults/preferences/.+\.js", filename))

    def js_tests(self):
        yield self.get_test(
                "password",
                "Passwords may be stored in `defaults/preferences/*.js`",
                "Storing passwords in the preferences JavaScript files is "
                "insecure. The Login Manager should be used insted.")


@register_generator
class BannedPrefRegexTests(RegexTestGenerator):
    """
    These regex tests will find whether banned preference branches are being
    referenced from outside preference JS files.

    Added from bug 676815
    """

    @classmethod
    def applicable(cls, err, filename, document):
        return not filename.startswith("defaults/preferences/")

    def tests(self):
        from javascript.predefinedentities import (BANNED_PREF_BRANCHES,
                                                   BANNED_PREF_REGEXPS)
        for pattern in BANNED_PREF_REGEXPS:
            yield self.get_test(
                    r"[\"']" + pattern,
                    "Potentially unsafe preference branch referenced",
                    "Extensions should not alter preferences matching /%s/."
                        % pattern)

        for branch in BANNED_PREF_BRANCHES:
            yield self.get_test(
                    branch.replace(r".", r"\."),
                    "Potentially unsafe preference branch referenced",
                    "Extensions should not alter preferences in the `%s` "
                    "preference branch" % branch)


@register_generator
class ChromePatternRegexTests(RegexTestGenerator):
    """
    Test that an Add-on SDK (Jetpack) add-on doesn't use interfaces that are
    not part of the SDK.

    Added from bugs 689340, 731109
    """

    def tests(self):
        # We want to re-wrap the test because if it detects something, we're
        # going to set the `requires_chrome` metadata value to `True`.
        def rewrap():
            wrapper = self.get_test(
                    r"(?<![\'\"])require\s*\(\s*[\'\"]"
                    r"(chrome|window-utils|observer-service)[\'\"]\s*\)",
                    "Usage of non-SDK interface",
                    "This SDK-based add-on uses interfaces that aren't part "
                    "of the SDK.")
            if wrapper():
                self.err.metadata["requires_chrome"] = True

        yield rewrap


@register_generator
class JSPrototypeExtRegexTests(RegexTestGenerator):
    """
    These regex tests will ensure that the developer is not modifying the
    prototypes of the global JS types.

    Added from bug 696172
    """

    @classmethod
    def applicable(cls, err, filename, document):
        return not (filename.endswith(".jsm") or "EXPORTED_SYMBOLS" in document)

    def js_tests(self):
        yield self.get_test(
                r"(String|Object|Number|Date|RegExp|Function|Boolean|Array|"
                r"Iterator)\.prototype(\.[a-zA-Z0-9]+|\[.+\]) =",
                "JS prototype extension",
                "It appears that an extension of a built-in JS type was made. "
                "This is not allowed for security and compatibility reasons.",
                flags=re.I)


class CompatRegexTestHelper(RegexTestGenerator):
    """
    A helper that makes it easier to stay DRY. This will automatically check
    for applicability against the value set as the app_versions_fallback.
    """

    def __init__(self, *args, **kwargs):
        super(CompatRegexTestHelper, self).__init__(*args, **kwargs)
        self.app_versions_fallback = self.VERSION

    @classmethod
    def applicable(cls, err, filename, document):
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
        yield self.get_test_bug(
                672507, "nsIAccessNode", DEP_INTERFACE,
                "The `nsIAccessNode` interface has been merged into "
                "`nsIAccessible`. You should use that interface instead.",
                compat_type="error")

        GLOBALSTORAGE_URL = ("https://developer.mozilla.org/en/XUL_School/"
                             "Local_Storage")
        yield self.get_test_bug(
                687579, "globalStorage",
                "`globalStorage` removed in Gecko 13",
                "As of Gecko 13, the `globalStorage` object has been removed. "
                "See %s for alternatives." % GLOBALSTORAGE_URL,
                compat_type="error")

        yield self.get_test_bug(
                702639, "excludeItemsIfParentHasAnnotation",
                "`excludeItemsIfParentHasAnnotation` no longer supported",
                "The `excludeItemsIfParentHasAnnotation` query option is no "
                "longer supported, as of Gecko 13.", compat_type="error")


@register_generator
class Gecko14RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 14 updates."""

    VERSION = FX14_DEFINITION

    def tests(self):
        BLOB_BUILDER_DEP = "`BlobBuilder` and `MozBlobBuilder` are deprecated."

        yield self.get_test_bug(
                736687, "(Moz)?BlobBuilder", BLOB_BUILDER_DEP,
                "The `BlobBuilder` and `MozBlobBuilder` objects are now "
                "deprecated. You should use the `Blob` constructor instead.",
                compat_type="warning")

        yield self.get_test_bug(
                682360, "nsILocalFile",
                "`nsILocalFile` should be replaced with `nsIFile`.",
                "Starting with Gecko 14, `nsILocalFile` inherits all functions "
                "and attributes from `nsIFile`, meaning that you no longer "
                "need to use `nsILocalFile`. If your add-on doesn't support "
                "versions older than 14, you should use `nsIFile` instead of "
                "`nsILocalFile`.", compat_type="warning")

        yield self.get_test_bug(
                737133, "onFaviconDataAvailable",
                "`onFaviconDataAvailable` renamed to `onComplete`.",
                "The `onFaviconDataAvailable` function has been renamed to "
                "`onComplete`. Also note that the function behaves slightly "
                "differently now.", compat_type="error")

        GUID_LINK = ("http://blog.bonardo.net/2012/02/16/"
                     "add-ons-devs-heads-up-we-are-killing-old-bookmarks-guids")
        yield self.get_test(
                "(getItemGUID|setItemGUID|getItemIdForGUID)",
                "`getItemGUID`, `setItemGUID`, and `getItemIdForGUID` were "
                "removed.",
                "Item GUIDs have been dropped from the Bookmarks Service. See "
                "%s for more information." % GUID_LINK, compat_type="error")

        yield self.get_test_bug(
                737841, "redirectsMode",
                "`redirectsMode` removed from `nsINavHistoryQueryOptions`",
                "The `redirectsMode` option has been removed from the "
                "`nsINavHistoryQueryOptions` interface. Error visits are no "
                "longer stored in the history, so it is no longer necessary.",
                compat_type="error")


@register_generator
class Gecko15RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 15 updates."""

    VERSION = FX15_DEFINITION

    def tests(self):

        yield self.get_test_bug(
                615213, "nsIGlobalHistory",
                "`nsIGlobalHistory` has been removed.",
                "The `nsIGlobalHistory` interface has been removed. You can "
                "use `nsIGlobalHistory2` instead.", compat_type="error")

        nISSWLink = ("https://blog.mozilla.org/nfroyd/2012/05/14/"
                         "statement-wrappers-have-been-deprecated/")
        yield self.get_test(
                "mozIStorageStatementWrapper",
                "`mozIStorageStatementWrapper` has been removed.",
                "The `mozIStorageStatementWrapper` interface has been removed. "
                "It is no longer necessary, you can use `mozIStorageStatement` "
                "directly instead. See %s for more information." % nISSWLink,
                compat_type="error")

        aPWDLink = ("https://developer.mozilla.org/en-US/docs/"
                        "XPCOM_Interface_Reference/nsIBrowserHistory"
                        "#addPageWithDetails%28%29")
        yield self.get_test(
                "addPageWithDetails",
                "`addPageWithDetails` has been removed.",
                "The `addPageWithDetails` function has been removed. You can "
                "use the equivalent `mozIAsyncHistory.updatePlaces` function "
                "instead. See %s for more information." % aPWDLink,
                compat_type="error")

        yield self.get_test_bug(
                730340, "(_DOMElement|_feedURI|_siteURI|_cellProperties)",
                "Private Properties removed from Places code.",
                "Places nodes no longer hold metadata in private properties. "
                "If you're using these properties to obtain Places data, this "
                "will no longer work.", compat_type="error")


@register_generator
class Thunderbird7RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 7 update."""

    VERSION = TB7_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                621213, r"resource:///modules/dictUtils.js",
                "`dictUtils.js` was removed in Thunderbird 7",
                "The `dictUtils.js` file is no longer available in "
                "Thunderbird as of version 7. You can use `Dict.jsm` "
                "instead.", compat_type="error")
        ab_patterns = [r"rdf:addressdirectory",
                       r"GetResource\(.*?\)\s*\.\s*"
                           r"QueryInterface\(.*?nsIAbDirectory\)",]
        for pattern in ab_patterns:
            yield self.get_test_bug(
                    621213, pattern,
                    "The address book does not use RDF in Thunderbird 7",
                    "The address book was changed to use a look up table in "
                    "Thunderbird 7. See %s for details." % TB7_LINK,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird10RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 10 update."""

    VERSION = TB10_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                700220, r"gDownloadManagerStrings",
                "`gDownloadManagerStrings` removed in Thunderbird 10",
                "The `gDownloadManagerStrings` global is no longer available "
                "in Thunderbird 10.", compat_type="error")
        yield self.get_test_bug(
                539997, r"nsTryToClose.js",
                "`nsTryToClose.js` removed in Thunderbird 10",
                "The `nsTryToClose.js` file is no longer available as of "
                "Thunderbird 10.", compat_type="error")


@register_generator
class Thunderbird11RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 11 update."""

    VERSION = TB11_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                39121, r"specialFoldersDeletionAllowed",
                "`specialFoldersDeletionAllowed` removed in Thunderbird 11",
                "The `specialFoldersDeletionAllowed` global was removed in "
                "Thunderbird 11.", compat_type="error",
                log_function=self.err.notice)

        patterns = {r"newToolbarCmd\.(label|tooltip)": 694027,
                    r"openToolbarCmd\.(label|tooltip)": 694027,
                    r"saveToolbarCmd\.(label|tooltip)": 694027,
                    r"publishToolbarCmd\.(label|tooltip)": 694027,
                    r"messengerWindow\.title": 701671,
                    r"folderContextSearchMessages\.(label|accesskey)": 652555,
                    r"importFromSeamonkey2\.(label|accesskey)": 689437,
                    r"comm4xMailImportMsgs\.properties": 689437,
                    r"specialFolderDeletionErr": 39121,
                    r"sourceNameSeamonkey": 689437,
                    r"sourceNameOExpress": 689437,
                    r"sourceNameOutlook": 689437,
                    r"failedDuplicateAccount": 709020,}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "Some code matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 11." % pattern,
                    compat_type="error")

        js_patterns = {r"onViewToolbarCommand": 644169,
                       r"nsContextMenu": 680192,
                       r"MailMigrator\.migrateMail": 712395,
                       r"AddUrlAttachment": 708982,
                       r"makeFeedObject": 705504,
                       r"deleteFeed": 705504, }
        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "Some code matched the JavaScript function `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 11." % pattern,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird12RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 12 update."""

    VERSION = TB12_DEFINITION

    def tests(self):
        yield self.get_test_bug(
                717240, r"EdImage(Map|MapHotSpot|MapShapes|Overlay)\.js",
                "`EdImage*.js` removed in Thunderbird 12",
                "`EdImageMap.js`, `EdImageMapHotSpot.js`, "
                "`EdImageMapShapes.js`, and `EdImageMapOverlay.js` were "
                "removed in Thunderbird 12.", compat_type="error",
                log_function=self.err.notice)

        patterns = {"editImageMapButton\.(label|tooltip)": 717240,
                    "haveSmtp[1-3]\.suffix2": 346306,
                    "EditorImage(Map|MapHotSpot)\.dtd": 717240,
                    "subscribe-errorInvalidOPMLFile": 307629, }
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "Some code matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 12." % pattern,
                    compat_type="error")

        js_patterns = {r"TextEditorOnLoad": 695842,
                       r"Editor(OnLoad|Startup|Shutdown|CanClose)": 695842,
                       r"gInsertNewIMap": 717240,
                       r"editImageMap": 717240,
                       r"(SelectAll|MessageHas)Attachments": 526998, }
        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "Some code matched the JavaScript function `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 12." % pattern,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird13RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 13 update."""

    VERSION = TB13_DEFINITION

    def tests(self):
        # String changes for add-ons depending on Thunderbird localizations.
        patterns = {"searchAllMessages\.(label|keyLabel2)": 728897,
                    "username(Desc|Label|SmtpDesc|SmtpLabel)\.(label|accesskey)": 71008,
                    "loginTitle\.label": 71008,
                    "smtpServer(Desc|Label)\.(label|accesskey)": 71008,
                    "incomingServer(NameDesc|Label)\.(label|accesskey)": 71008,
                    "serverTitle\.label": 71008,
                    "location\.label": 716706,
                    "feed-properties\.dtd": 716706,}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 13." % pattern,
                    compat_type="error")

        js_patterns = {r"webSearchProvider\.js": 733802,
                       r"general\.useragent\.extra\.thunderbird": 726942,
                       r"gPermissionManager\._updatePermissions": 728810,
                       r"(gPromptService|gHeaderParser)": 722187,
                       r"setup(Cc|Bcc)Textbox": 208628,
                       r"onBiffMinChange": 532391,
                       r"(server|login)Page(Validate|Unload|Init)": 71008,
                       r"feed-properties\.js": 716706,
                       r"gFeedSubscriptionsWindow\.(init|uninit)": 716706,
                       r"openComposeWindowForRSSArticle": 716706,
                       r"nsOfflineStartupModule\.getBundle": 722168,
                       r"GetOnlineDelimiter": 301714, }
        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "A javascript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 13." % pattern,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird14RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 14 update."""

    VERSION = TB14_DEFINITION

    def tests(self):
        # String changes for add-ons depending on Thunderbird localizations.
        patterns = {r"spellCheck(IgnoreWord|NoSuggestions|AddToDictionary)\."
                        "(label|accesskey)": 735986,
                    r"account(Title|SettingsDesc)\.label": 340324,
                    r"messageStorage\.label": 340324,
                    r"emptyTrashOnExit\.(label|accesskey)": 340324,
                    r"local(Path|FolderPicker)\.label": 340324,
                    r"browseFolder\.(label|accesskey)": 340324,
                    r"replyNewsgroupCmd\.(label|accesskey)": 718342,
                    r"contextReplyNewsgroup\.(label|accesskey)": 718342,
                    r"junkLog(Info|)\.(title|label)": 323159,
                    r"enableJunkLogging\.(label|accesskey)": 323159,}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 14." % pattern,
                    compat_type="error")

        js_patterns = {r"feed-subscriptions\.js": 737115,
                       r"(\b|\()msgComposeService": 739051,
                       r"(\b|\()IsCanSearchMessagesEnabled": 537378,
                       r"(\b|\()(g|cv)(Prefs|IOService|HeaderParser)": 733496,
                       r"(\b|\()(nsPrefBranch|CollapseSectionSeparators)": 713277,
                       r"(\b|\()g(PrefBranch|MailSession)": 736870,
                       r"(\b|\()gIncomingServer": 340324,
                       r"(\b|\()getPromptService": 732807,
                       r"mailnews\.display\.html_sanitizer\.allowed_tags": 650776,
                       r"downloadheaders\.js": 732811,
                       r"(\b|\()kSmallCommit": 747102,}
        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "A javascript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 14." % pattern,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird15RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 15 update."""

    VERSION = TB15_DEFINITION

    def tests(self):
        # String changes for add-ons depending on Thunderbird localizations.
        patterns = {r"hdrReplyButton1\.tooltip": 747298,
                    r"ScreenName\.(label|accesskey)": 759328,
                    r"searchAllChatMessages\.label\.base": 743235,
                    r"accountsWindow\.style": 742674,
                    r"smtpDesc\.label": 391061,
                    r"trainingWarning\.label": 397197,
                    r"whitelist\.(label|accesskey)": 397197,
                    r"update\.restart\.applyButton\.(label|accesskey)": 755968,
                    r"junkBarMessage1\.label": 590226,}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 15." % pattern,
                    compat_type="error")

        prefix_patterns = {r"FZ_(FEED|QUICKMODE|DESTFOLDER|"
                            "STORED|VALID|LAST_SEEN_TIMESTAMP)": 721517,
                           r"RDF_(TYPE|LITERAL_TRUE|LITERAL_FALSE)": 721517,
                           r"DC_(NS|CREATOR|SUBJECT|DATE|TITLE"
                            "|LASTMODIFIED|IDENTIFIER)": 721517,
                           r"RSS_(NS|CHANNEL|TITLE|DESCRIPTION|ITEMS|"
                            "ITEM|LINK|CONTENT_NS|CONTENT_ENCODED)": 721517,
                           r"ATOM_(03_NS|IETF_NS)": 721517,
                           r"INVALID_ITEM_PURGE_DELAY": 721517,
                           r"kFeedUrlDelimiter": 721517,
                           r"get(FeedUrlsInFolder|NodeValue|RDFTargetValue|"
                            "ParentTargetForChildResource)": 721517,                        
                           r"getSubscriptions(DS|List|File)": 721517,
                           r"getItems(DS|File)": 721517,
                           r"(add|delete)Feed": 721517,
                           r"initAcountActionsButton": 739573,
                           r"gFeedSubscriptionsWindow": 750292,
                           r"showIMConversationInTab": 743235,
                           r"waitForBuddyInfo": 753807,
                           r"(updateFolderFeedURL|containerUtils)": 721517,}

        js_patterns = {r"debug-utils\.js": 721517,
                       r"Configurator": 735524,  # Intentional unrestricted substring.
                       r"\.capabilityPref": 558659,}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns.update(dict(("(\b|\()" + k, v) for k, v in prefix_patterns.items()))

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "A javascript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 15." % pattern,
                    compat_type="error", log_function=self.err.notice)

