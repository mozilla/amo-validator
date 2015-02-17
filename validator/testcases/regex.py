import re
from functools import wraps

from validator.constants import BUGZILLA_BUG, MDN_DOC
from validator.compat import (
    FX5_DEFINITION, FX6_DEFINITION, FX7_DEFINITION, FX8_DEFINITION,
    FX9_DEFINITION, FX11_DEFINITION, FX12_DEFINITION, FX13_DEFINITION,
    FX14_DEFINITION, FX15_DEFINITION, FX16_DEFINITION, FX17_DEFINITION,
    FX18_DEFINITION, FX19_DEFINITION, FX20_DEFINITION, FX21_DEFINITION,
    FX22_DEFINITION, FX23_DEFINITION, FX24_DEFINITION, FX25_DEFINITION,
    FX26_DEFINITION, FX27_DEFINITION, FX28_DEFINITION, FX30_DEFINITION,
    FX31_DEFINITION, FX32_DEFINITION, FX34_DEFINITION, FX36_DEFINITION,
    TB7_DEFINITION, TB10_DEFINITION, TB11_DEFINITION, TB12_DEFINITION,
    TB13_DEFINITION, TB14_DEFINITION, TB15_DEFINITION, TB16_DEFINITION,
    TB17_DEFINITION, TB18_DEFINITION, TB19_DEFINITION, TB20_DEFINITION,
    TB21_DEFINITION, TB22_DEFINITION, TB23_DEFINITION, TB24_DEFINITION,
    TB25_DEFINITION, TB26_DEFINITION, TB27_DEFINITION, TB28_DEFINITION,
    TB29_DEFINITION, TB30_DEFINITION, TB31_DEFINITION)
from validator.contextgenerator import ContextGenerator
from markup.csstester import UNPREFIXED_MESSAGE


registered_regex_tests = []


NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."
NSINHS_LINK = MDN_DOC % "XPCOM_Interface_Reference/nsINavHistoryService"


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
        @wraps(log_function)
        def wrapper():
            matched = False
            for match in re.finditer(pattern, self.document, flags):
                log_function(
                    **{'err_id': ("testcases_regex", "generic", "_generated"),
                       log_function.__name__: title,
                       'description': message,
                       'filename': self.filename,
                       'line': self.context.get_line(match.start()),
                       'context': self.context,
                       'compatibility_type': compat_type,
                       'for_appversions': app_versions,
                       'tier': self.err.tier if app_versions is None else 5})
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

    def js_tests(self):
        yield self.get_test(
                "mouse(move|over|out)",
                "Mouse events may cause performance issues.",
                "The use of `mousemove`, `mouseover`, and `mouseout` is "
                "discouraged. These events are dispatched with high frequency "
                "and can cause severe performance issues.",
                log_function=self.err.warning)


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
class MarionetteInPrefsRegexTests(RegexTestGenerator):
    """
    These regex tests will ensure that the developer is not switching on
    Marionette prefs

    Added from bug 741812
    """

    MARIONETTE_REFERENCES = {r"@mozilla\.org/marionette;1": 741812,
                        r"\{786a1369\-dca5\-4adc-8486\-33d23c88010a\}": 741812,
                        "MarionetteComponent": 741812,
                        "MarionetteServer": 741812}

    MARIONETTE_PREFS = {r"marionette\.force\-local": 741812,
                        r"marionette\.defaultPrefs\.enabled": 741812,
                        r"marionette\.defaultPrefs\.port": 741812}
    @classmethod
    def applicable(cls, err, filename, document):
        return bool(re.match(r"defaults/preferences/.+\.js", filename))

    def js_tests(self):
        title = "Marionette access is disallowed"
        for ref, bug in self.MARIONETTE_REFERENCES.items():
            print ref
            yield self.get_test_bug(
                    bug, ref, title,
                    "Marionette references are not allowed as it could lead to"
                    "the browser not being secure. Please remove them.")

        for ref, bug in self.MARIONETTE_PREFS.items():
            print ref
            yield self.get_test_bug(
                    bug, ref, title,
                    "Marionette preferences are not allowed as it could lead to"
                    "the browser not being secure. Please remove them.")


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
                "insecure. The Login Manager should be used instead.")


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

        for branch, reason in BANNED_PREF_BRANCHES:
            yield self.get_test(
                    branch.replace(r".", r"\."),
                    "Potentially unsafe preference branch referenced",
                    reason or ("Extensions should not alter preferences in "
                               "the `%s` preference branch" % branch))


REQUIRE_PATTERN = (r"""(?<!['"])require\s*\(\s*['"]"""
                   r"""(?:sdk/)?(%s)['"]\s*\)""")


@register_generator
class UnsafeTemplateRegexTests(RegexTestGenerator):
    """
    Checks for the use of unsafe template escape sequences.
    """

    @classmethod
    def applicable(cls, err, filename, document):
        # Perhaps this should just run on all non-binary files, but
        # we'll try to be more selective for the moment.
        return bool(re.match(r".*\.(js(|m)|handlebars|mustache|"
                             r"(t|)htm(|l)|tm?pl)",
                             filename))

    def tests(self):
        for unsafe, safe in (('<%=', '<%-'),
                             ('{{{', '{{'),
                             ('ng-bind-html-unsafe=', 'ng-bind-html')):
            yield self.get_test(
                    re.escape(unsafe),
                    "Potentially unsafe template escape sequence",
                    "The use of non-HTML-escaping template escape sequences is "
                    "potentially dangerous and highly discouraged. Non-escaped "
                    "HTML may only be used when properly sanitized, and in most "
                    "cases safer escape sequences such as `%s` must be used "
                    "instead." % safe)


@register_generator
class ChromePatternRegexTests(RegexTestGenerator):
    """
    Test that an Add-on SDK (Jetpack) add-on doesn't use interfaces that are
    not part of the SDK.

    Added from bugs 689340, 731109, 845492
    """

    INTERFACES = "|".join([
        # Added from bugs 689340, 731109
        "chrome", "window-utils", "observer-service",
        # Added from bug 845492
        "window/utils", "sdk/window/utils", "sdk/deprecated/window-utils",
        "tab/utils", "sdk/tab/utils",
        "system/events", "sdk/system/events",
    ])

    def tests(self):
        # We want to re-wrap the test because if it detects something, we're
        # going to set the `requires_chrome` metadata value to `True`.
        def rewrap():
            wrapper = self.get_test(
                    REQUIRE_PATTERN % self.INTERFACES,
                    "Usage of flagged or non-SDK interface",
                    "This SDK-based add-on uses interfaces that aren't part "
                    "of the SDK or are flagged as sensitive.")
            if wrapper():
                self.err.metadata["requires_chrome"] = True

        yield rewrap


@register_generator
class WidgetModuleRegexTests(RegexTestGenerator):
    """
    Tests whether an Add-on SDK add-on is using the deprecated widget
    interface.
    """

    def js_tests(self):
        yield self.get_test(
            REQUIRE_PATTERN % "widget",
            "Use of deprecated SDK module",
            "The 'widget' module has been deprecated due to a number of "
            "performance and usability issues, and is slated to be removed "
            "from the SDK in the near future. Please use the "
            "'sdk/ui/button/action' or 'sdk/ui/button/toggle' module "
            "instead. See "
            "https://developer.mozilla.org/Add-ons/SDK/High-Level_APIs/ui "
            "for more information.")


@register_generator
class ExtensionManagerRegexTests(RegexTestGenerator):
    """
    Tests for uses of the old extension manager API, which should not be
    referenced in new extensions.
    """

    def js_tests(self):
        yield self.get_test(
                r"@mozilla\.org/extensions/manager;1|"
                r"em-action-requested",
                "Obsolete Extension Manager API",
                "The old Extension Manager API is not available in any "
                "remotely modern version of Firefox and should not be "
                "referenced in any code.")


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
                "versions of Gecko, you should stop using nsIPrefBranch2.",
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

        aPWDLink = (MDN_DOC % "XPCOM_Interface_Reference/nsIBrowserHistory"
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
class Gecko16RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 16 updates."""

    VERSION = FX16_DEFINITION

    def tests(self):

        yield self.get_test(
                "nsITransferable",
                "`nsITransferable` has been changed in Gecko 16.",
                "The `nsITransferable` interface has changed to better "
                "support Private Browsing Mode. After instantiating the "
                "object, you should call the `init` function on it before "
                "any other functions are called. See %s for more "
                "information." % MDN_DOC % "Using_the_Clipboard",
                compat_type="error")

        yield self.get_test_bug(
                726378, "mozIndexedDB",
                "`mozIndexedDB` has been unprefixed in Gecko 16.",
                "The `mozIndexedDB` object has been renamed to `indexedDB` in "
                "Firefox 16.", compat_type="error")

    def js_tests(self):

        yield self.get_test(
                "Moz(Transition|Animation|Transform)[a-zA-Z]+",
                "Some CSS selectors have been unprefixed in Gecko 16.",
                UNPREFIXED_MESSAGE, compat_type="warning")


@register_generator
class Gecko17RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 17 updates."""

    VERSION = FX17_DEFINITION

    CFMM_URL = ("http://mxr.mozilla.org/mozilla-beta/source/content/base/"
                "public/nsIMessageManager.idl")

    def js_tests(self):

        yield self.get_test_bug(
                776825, "nsIChromeFrameMessageManager",
                "`nsIChromeFrameMessageManager` has been removed.",
                "The `nsIChromeFrameMessageManager` interface has been "
                "removed, and the new Message Manager interfaces should be "
                "used instead. See %s for more information." % self.CFMM_URL,
                compat_type="error")

        yield self.get_test_bug(
                761278, "onuploadprogress",
                "`onuploadprogress` has been removed.",
                "The `onuploadprogress` property has been removed from "
                "`XMLHttpRequest`.", compat_type="error")

        yield self.get_test_bug(
                327244, "checkLoadURI(Str)?",
                "`checkLoadURI` and `checkLoadURIStr` have been removed.",
                "The `checkLoadURI` and `checkLoadURIStr` interfaces have "
                "been removed. You should use `checkLoadURIWithPrincipal` "
                "instead.", compat_type="error")


@register_generator
class Gecko18RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 18 updates."""

    VERSION = FX18_DEFINITION

    def js_tests(self):

        yield self.get_test_bug(
                794602, "saveURI",
                "`saveURI` has been changed.",
                "The `saveURI` function have changed to support per-window "
                "private browsing. You should now pass a context as an "
                "additional argument.",
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
                769764,
                "nsIProtocolProxyService|nsIProxyAutoConfig|newProxiedChannel",
                "Proxy interfaces have been changed.",
                "The `nsIProtocolProxyService` and `nsIProxyAutoConfig` "
                "interfaces, as well as the `newProxiedChannel` function have "
                "changed in order to make the proxy API asynchronous.",
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
                722861, "imgI(Cache|Loader)",
                "`imgICache` and `imgILoader` have been deprecated.",
                "The `imgICache` and `imgILoader` interfaces have been "
                "deprecated in Gecko 18. You should use `imgITools` instead. "
                "See %s for more information." %
                    MDN_DOC % "XPCOM_Interface_Reference/imgICache",
                compat_type="error")

        yield self.get_test_bug(
                774963, "removeDataFromDomain",
                "`removeDataFromDomain` has been moved.",
                "The `removeDataFromDomain` function has been moved to "
                "`ClearRecentHistory.jsm`.",
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
                695399, "openCacheEntry",
                "`openCacheEntry` no longer works from main thread.",
                "The `openCacheEntry` function no longer works when invoked "
                "from the main thread. You should use `asyncOpenCacheEntry` "
                "instead.",
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
                744907, "BlobBuilder",
                "`BlobBuiler` has been removed.",
                "The `BlobBuilder` object has been removed. You should use "
                "the `Blob` constructor instead. See %s for more "
                "information." % MDN_DOC % "DOM/BlobBuilder",
                compat_type="error")

        yield self.get_test_bug(
                741059, "setAndLoadFaviconForPage",
                "`setAndLoadFaviconForPage` has been changed.",
                "The `setAndLoadFaviconForPage` function have changed to "
                "support per-window private browsing. You should now pass a "
                "load type as an additional argument.",
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
                795065, "addDownload|saveURL",
                "`addDownlod` and `saveURL` have been changed.",
                "The `addDownload` and `saveURL` functions have changed to "
                "support per-window private browsing. You should now pass an "
                "additional argument to them.",
                compat_type="error", log_function=self.err.notice)


@register_generator
class Gecko19RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 19 updates."""

    VERSION = FX19_DEFINITION

    def js_tests(self):

        yield self.get_test_bug(
            723002, "nsIContentPrefService",
            "`nsIContentPrefService` has been changed.",
            "`nsIContentPrefService` has been changed to support "
            "per-window private browsing. Most of its functions now "
            "require an additional argument to specify a context.",
            compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
            664695, "getMessageArray",
            "`nsIConsoleService::getMessageArray` has been changed.",
            "The `getMessageArray` function has changed, and now it returns "
            "the array instead of setting the object passed as a parameter.",
            compat_type="error", log_function=self.err.notice)


@register_generator
class Gecko20RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 20 updates."""

    VERSION = FX20_DEFINITION
    PRIVATE_BROWSING_LINK = MDN_DOC % "Updating_addons_broken_by_private_browsing_changes"
    DECODE_LINK = BUGZILLA_BUG % 816362
    EDITABLE_LINK = BUGZILLA_BUG % 827546
    PROFILE_LINK = BUGZILLA_BUG % 807757
    PLACES_IMPORT_LINK = BUGZILLA_BUG % 763295

    def js_tests(self):

        for pbs in ("nsIPrivateBrowsingService", "private-browsing"):
            yield self.get_test_bug(
                826079, pbs,
                "`nsIPrivateBrowsingService` has been removed.",
                "`nsIPrivateBrowsingService` and its related observer "
                "notifications have been removed due to the new per-window "
                "private browsing mode. See {0} for more "
                "information.".format(self.PRIVATE_BROWSING_LINK),
                compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
            816362, "decodeImageData",
            "`decodeImageData` has been deprecated.",
            "decodeImageData has been deprecated. You should instead use "
            "decodeImage, from the same interface. See {0} for more "
            "information.".format(self.DECODE_LINK),
            compat_type="warning", log_function=self.err.notice)

        yield self.get_test_bug(
            827546, "nsIDOMNSEditableElement",
            "In Firefox 20, using `QueryInterface` of a non-editable element "
            "to `nsIDOMNSEditableElement` doesn't throw an exception as "
            "expected.",
            "In Firefox 20, using `QueryInterface` of a non-editable element "
            "to `nsIDOMNSEditableElement` doesn't throw an exception as "
            "expected. This has been fixed in Firefox 21. Using `instanceof` "
            "is the recommended way of doing this, which avoids this error. "
            "See {0} for more information.'".format(self.EDITABLE_LINK),
            compat_type="warning", log_function=self.err.notice)


        yield self.get_test_bug(
            807757, "nsIProfile",
            "`nsIProfile` and `nsIProfileChangeStatus` have been removed.",
            "`nsIProfile` and `nsIProfileChangeStatus` have been removed "
            "because they weren't in use anymore. See {0} for more "
            "information.".format(self.PROFILE_LINK),
            compat_type="error", log_function=self.err.notice)

        yield self.get_test_bug(
            763295, "nsIPlacesImportExportService",
            "`nsIProfile` and `nsIProfileChangeStatus` have been removed.",
            "`nsIPlacesImportExportService`` was removed. You can use "
            "`BookmarkHTMLUtils.jsm` "
            "(resource://gre/modules/BookmarkHTMLUtils.jsm) instead. See {0} "
            "for more information.".format(self.PLACES_IMPORT_LINK),
            compat_type="error", log_function=self.err.notice)


@register_generator
class Gecko21RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 21 updates."""

    VERSION = FX21_DEFINITION

    def js_tests(self):

        for pattern in (
                "resource:///modules/.*",
                r"resource://gre/modules/(HUDService|MigrationUtils|"
                    "PlacesUIUtils|PropertyPanel|RecentWindow|offlineAppCache|"
                    "source-editor)\.jsm"):
            yield self.get_test_bug(
                763295, pattern,
                "Some JS Modules were moved to a different location.",
                "Some JS modules were moved from `resource:///` and "
                "`resource://gre/` to `resource://app/`.",
                compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            835543, "(RESULT_TYPE_DYNAMIC_CONTAINER|RESULT_TYPE_FULL_VISIT)",
            "`nsINavHistoryService` members removed.",
            "`RESULT_TYPE_DYNAMIC_CONTAINER` and `RESULT_TYPE_FULL_VISIT` "
            "were removed.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            826409, "(onBeforeDeleteURI|onBeforeItemRemoved)",
            "Event handlers removed in Gecko 21",
            "`onBeforeDeleteURI` and `onBeforeItemRemoved` were removed.",
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko22RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 22 updates."""

    VERSION = FX22_DEFINITION

    NSIGH2_LINK = MDN_DOC % "XPCOM_Interface_Reference/mozIAsyncHistory"
    NSIBH_LINK = MDN_DOC % "XPCOM_Interface_Reference/nsINavHistoryService"
    NSIFS_LINK = MDN_DOC % "XPCOM_Interface_Reference/mozIAsyncFavicons"
    NSITV_LINK = "https://hg.mozilla.org/mozilla-central/rev/bf88a316cf18#l17.18"
    NSIPV_LINK = MDN_DOC % "Supporting_per-window_private_browsing"

    def js_tests(self):

        yield self.get_test_bug(
            838874, "(nsIGlobalHistory2|addURI|isVisited|setPageTitle)",
            "`nsIGlobalHistory2` no longer implemented.",
            "`nsIGlobalHistory2` and its functions are no longer available. "
            "See %s for information about alternative functions." %
                self.NSIGH2_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            838798, "(nsILivemarkService|itemIsLivemark|"
                    "nodeIsLivemarkContainer|nodeIsLivemarkItem)",
            "`nsILivemarkService` removed along with `PlacesUtisl` members.",
            "The `nsILivemarkService` interface and related functions were "
            "removed, in favor of its asynchronous alternatives.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            839034, "(markPageAsTyped|markPageAsFollowedLink)",
            "`nsIBrowserHistory` members moved.",
            "`markPageAsTyped` and `markPageAsFollowedLink` were moved from "
            "`nsIBrowserHistory` to `nsINavHistoryService`. See %s for more "
            "information." % self.NSIBH_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            838839, "(setFaviconUrlForPage|setAndLoadFaviconForPage|"
                    "setFaviconData|setFaviconDataFromDataURL|getFaviconData|"
                    "getFaviconDataAsDataURL|getFaviconForPage|"
                    "getFaviconImageForPage)",
            "`nsIFaviconService` members removed.",
            "Several deprecated functions were removed from "
            "`nsIFaviconService`. See %s for supported alternatives." %
                self.NSIFS_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            407956, "(getRowProperties|getCellProperties|getColumnProperties)",
            "`nsITreeView` interface was changed to remove all "
            "`nsISupportsArray` usage.",
            "These functions from `nsITreeView` have changed. They now return "
            "a whitespace delimited string. See %s for more information." %
                self.NSITV_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            845063, "nsIPrivateBrowsingService",
            "`nsIPrivateBrowsingService` was removed.",
            "`nsIPrivateBrowsingService` was removed. See %s for more "
            "information." % self.NSIPV_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            858185, "fullZoom",
            "`fullZoom` property was changed.",
            "Setting the `fullZoom` property can yield unexpected results in "
            "Gecko 22 and above.",
            compat_type="error")

        yield self.get_test_bug(
            842372, "(g|s)etUserData",
            "`getUserData` and `setUserData are now restricted.",
            "`getUserData` and `setUserData are now restricted. They can no "
            "longer be used for content code.",
            compat_type="warning", log_function=self.err.notice)

        yield self.get_test_bug(
            480356, "FillInHTMLTooltip",
            "`FillInHTMLTooltip` was moved.",
            "`FillInHTMLTooltip` was moved to the tooltip object and is now "
            "called `fillInPageTooltip`. It still works as a compatibility "
            "shim, but its usage is deprecated.",
            compat_type="warning", log_function=self.err.notice)


@register_generator
class Gecko23RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 23 updates."""

    VERSION = FX23_DEFINITION

    LOAD_LINK = MDN_DOC % "XUL/School_tutorial/Intercepting_Page_Loads"
    USFUC_LINK = MDN_DOC % "XPCOM_Interface_Reference/nsIAboutModule"

    def js_tests(self):

        yield self.get_test_bug(
            851586, "URI_SAFE_FOR_UNTRUSTED_CONTENT",
            "`URI_SAFE_FOR_UNTRUSTED_CONTENT` restricted in Gecko 23.",
            "`URI_SAFE_FOR_UNTRUSTED_CONTENT` can now only be used if your "
            "`about:` page only has unprivileged HTML code. It can't be used "
            "with XUL code anymore. We recommend that you stop using the "
            "`URI_SAFE_FOR_UNTRUSTED_CONTENT` flag entirely. See %s for more "
            "information." % self.USFUC_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            859586, "\"(Start|End|Fail)DocumentLoad\"",
            "Document load notifications removed in Gecko 23.",
            "`\"StartDocumentLoad\"`, `\"EndDocumentLoad\"`, and "
            "`\"FailDocumentLoad\"` were removed in Gecko 23. You can use "
            "other, more standard event handlers instead. See %s for more "
            "information." % self.LOAD_LINK,
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko24RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 24 updates."""

    VERSION = FX24_DEFINITION

    DOM_LINK = MDN_DOC % "Web/API/event.stopPropagation"
    GPD_LINK = MDN_DOC % "Web/API/event.defaultPrevented"

    def js_tests(self):

        yield self.get_test_bug(
            867432, r"verifyForUsage\(",
            "`nsIX509Cert.verifyForUsage` was removed.",
            "`nsIX509Cert.verifyForUsage` was removed in Gecko 24.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            874003, r"prevent(Bubble|Capture)",
            "`preventBubble` and `preventCapture` were removed.",
            "`preventBubble` and `preventCapture` were removed in Gecko 24. "
            "You can use `stopPropagation` instead. See %s for more "
            "information." % self.DOM_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            726933, r"getPreventDefault",
            "`getPreventDefault` is deprecated.",
            "The `getPreventDefault` function is deprecated. Use the "
            "`defaultPrevented` property instead. See %s for more "
            "information." % self.GPD_LINK,
            compat_type="warning", log_function=self.err.notice)

        yield self.get_test_bug(
            673919, r"routeEvent",
            "`routeEvent` was removed.",
            "The `routeEvent` function was removed in Gecko 24.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            673919, r"(enableExternalCapture|disableExternalCapture)",
            "`enableExternalCapture` and `disableExternalCapture` were "
            "removed.",
            "The `enableExternalCapture` and `disableExternalCapture` "
            "functions were removed in Gecko 24.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            879118, r"nsIFormHistory2",
            "`nsIFormHistory2` is deprecated.",
            "The `nsIFormHistory2` interface is deprecated. The "
            "`FormHistory.jsm` module should be used instead.",
            compat_type="warning", log_function=self.err.notice)

        yield self.get_test_bug(
            882079, r"nsIDocShellHistory",
            "nsIDocShellHistory` interface was merged into `nsIDocShell`.",
            "The `nsIDocShellHistory` interface was merged into "
            "`nsIDocShell`. Use `nsIDocShell` instead.",
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko25RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 25 updates."""

    VERSION = FX25_DEFINITION

    def js_tests(self):

        yield self.get_test_bug(
            846635, r"getShortcutOrURI",
            "`getShortcutOrURI` was removed.",
            "`getShortcutOrURI` was replaced in favor of the asynchronous "
            "`getShortcutOrURIAndPostData` in Gecko 25.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            846635, r"_canonizeURL",
            "`_canonizeURL` is now asynchronous in Gecko 25.",
            "`_canonizeURL` is asynchronous as of Gecko 25.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            776708, r"findbar.xml",
            "`findbar.xml` has changed in Gecko 25.",
            "The findbar binding was significantly changed and could break "
            "any of its consumers.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            895839, r"(getAnnotationURI|(get|set)(Page|Item)AnnotationBinary)",
            "Binary annotations were removed in Gecko 25.",
            "Binary annotations have been discontinued, so this function no "
            "longer exists.",
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko26RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 26 updates."""

    VERSION = FX26_DEFINITION

    DLM_LINK = MDN_DOC % "Mozilla/JavaScript_code_modules/Downloads.jsm"
    HME_LINK = MDN_DOC % "XPCOM_Interface_Reference/nsISHEntry"
    WH_LINK = MDN_DOC % "Web/API/Window.history"

    def js_tests(self):

        yield self.get_test_bug(
            847863, r"nsIDownloadManager",
            "`nsIDownloadManager` is now deprecated.",
            "`nsIDownloadManager` is deprecated. You should use Downloads.jsm "
            "instead. See %s for more information." % self.DLM_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            910517, r"nsIMemory(Multi)?Reporter(Callback|Manager)?",
            "Some memory reporting interfaces have been changed.",
            "The memory reporting interfaces have changed to remove "
            "uni-reporters.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            910161, r"nsIHistoryEntry",
            "`nsIHistoryEntry` has been replaced.",
            "`nsIHistoryEntry` has been replaced with `nsISHEntry` in Gecko "
            "26. See %s for more information." % self.HME_LINK,
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            904460, r"_firstTabs",
            "`_firstTabs` has been removed.",
            "`_firstTabs` has been removed and is now passed as an argument to "
            "the `restoreWindow()` function.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            856437, r"lookupMethod",
            "`Components.lookupMethod` has been removed.",
            "`Components.lookupMethod` has been removed. The behavior "
            "implemented by this function now happens automatically, so it is "
            "unnecessary now.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            846185, r"nsIAccessibleProvider",
            "`nsIAccessibleProvider` has been removed.",
            "`nsIAccessibleProvider` has been removed. You should remove its "
            "references from your bindings and use the role attribute "
            "instead.",
            compat_type="error", log_function=self.err.warning)

        yield self.get_test_bug(
            903311, r"history(\.current|\.previous|\.next|\[.+\])",
            "Non-standard `window.history` members have been removed.",
            "A few non-standard properties in `window.history` have been "
            "removed. You should use the standard equivalents instead. See %s "
            "for more information." % self.WH_LINK,
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko27RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 27 updates."""

    VERSION = FX27_DEFINITION

    BUG_ID = 845408

    def js_tests(self):

        yield self.get_test_bug(
            self.BUG_ID, r"downloads-indicator",
            "The `#downloads-indicator` node was removed from the DOM.",
            "The `#downloads-indicator` node was removed from the DOM. You "
            "should be able to use `#downloads-button` instead. See %s for "
            "more information." % BUGZILLA_BUG % self.BUG_ID,
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko28RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 28 updates."""

    VERSION = FX28_DEFINITION
    BUG_ID = 867097

    def js_tests(self):
        yield self.get_test_bug(
            self.BUG_ID, r"__SS_tabStillLoading",
            "The `__SS_tabStillLoading` property was removed.",
            "The `__SS_tabStillLoading` property was removed. You can "
            "check the existence of `__SS_data` instead. See %s for more "
            "information." % BUGZILLA_BUG % self.BUG_ID,
            compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko30RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 30 updates."""

    VERSION = FX30_DEFINITION
    BUG_ID = 952307

    def js_tests(self):
        filenames = [
            "AddonRepository.jsm",
            "LightweightThemeImageOptimizer.jsm",
            "XPIProvider.jsm",
            "AddonUpdateChecker.jsm",
            "AddonLogging.jsm",
            "PluginProvider.jsm",
            "AddonRepository_SQLiteMigrator.jsm",
            "XPIProviderUtils.js",
            "SpellCheckDictionaryBootstrap.js",
        ]

        for filename in filenames:
            yield self.get_test_bug(
                self.BUG_ID,
                "resource://gre/modules/{name}".format(name=filename),
                "Some JS modules were moved to a different location.",
                "These JS modules were moved to a different location. You "
                "need to change their import path to this: "
                "resource://gre/modules/addons/{name}"
                .format(name=filename),
                compat_type="error", log_function=self.err.warning)


@register_generator
class Gecko31RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 31 updates."""

    VERSION = FX31_DEFINITION

    def tests(self):
        yield self.get_test_bug(
            1033705,
            "browser\.tabs\.closeButtons",
            'The "browser.tabs.closeButtons" preference has been removed.',
            'The "browser.tabs.closeButtons" preference has been removed.',
            compat_type="warning",
            log_function=self.err.warning)

        mdn_article = "How_to_implement_custom_autocomplete_search_component"
        yield self.get_test(
            "nsIAutoCompleteResult",
            "`nsIAutoCompleteResult` has changed",
            "The `nsIAutoCompleteResult` interfaces were changed, introducing "
            "the getFinalCompleteValueAt function. See %s for more "
            "information." % MDN_DOC % mdn_article,
            compat_type="warning",
            log_function=self.err.warning)


@register_generator
class Gecko32RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 32 updates."""

    VERSION = FX32_DEFINITION

    def tests(self):
        from validator.testcases.javascript.entity_values import (
            FX32_BLOG, FX32_MDN)
        yield self.get_test(
            r'\bnsICache\b',
            "nsICache has been removed",
            "nsICache has been removed. See {blog} and {mdn} for more "
            "information.".format(blog=FX32_BLOG, mdn=FX32_MDN),
            log_function=self.err.warning,
            compat_type="error")


@register_generator
class Gecko34RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 34 updates."""

    VERSION = FX34_DEFINITION

    def tests(self):
        yield self.get_test(
            r"\bnsICommandParams\b",
            "nsICommandParams instances no longer support enumeration.",
            "nsICommandParams instances no longer support enumeration. If "
            "you're using hasMoreElements(), first() or getNext(), you'll "
            "need to change your code to use the other getter functions. See "
            "{bug} for more information.".format(bug=BUGZILLA_BUG % 1057914),
            log_function=self.err.warning,
            compat_type="warning")

        hg = "https://hg.mozilla.org/mozilla-central/rev/25c918c5f3e1#l18.3"
        yield self.get_test(
            "(['\"]rdf:local-store['\"]|PlacesUIUtils.localStore)",
            "The RDF implementation of local storage has been removed.",
            "The RDF implementation of local storage has been removed. You "
            "can use the nsIXULStore component instead. See {hg} and {bug} "
            "for more information.".format(hg=hg, bug=BUGZILLA_BUG % 559505),
            log_function=self.err.warning,
            compat_type="error")

        yield self.get_test(
            r"['\"][^'\"]*GreD[^'\"]*['\"]",
            "The \"GreD\" directory was split in two on Mac OS X.",
            "The \"GreD\" directory was split in two on Mac OS X, so some "
            "files are no longer accessible through that reference. If you "
            "used this directory to access binary files, you need to use "
            "\"GreBinD\" instead. See {bug} for more information.".format(
                bug=BUGZILLA_BUG % 1077099),
            log_function=self.err.warning,
            compat_type="warning")

        yield self.get_test(
            r"\bnsIMarkupDocumentViewer\b",
            "The nsIMarkupDocumentViewer interface has been removed.",
            "The nsIMarkupDocumentViewer interface has been removed. All of "
            "its functionality has been moved to the nsIContentViewer "
            "interface. See {bug} for more information.".format(
                bug=BUGZILLA_BUG % 1036694),
            log_function=self.err.warning,
            compat_type="error")

        yield self.get_test(
            r"\b(set|get)CharsetForURI\b",
            "The setCharsetForURI and getCharsetForURI functions have been "
            "removed from the history service.",
            "The setCharsetForURI and getCharsetForURI functions have been "
            "removed from the history service. You can use the equivalent "
            "functions in the PlacesUtils module instead. See {bug}#c3 for "
            "more information.".format(bug=BUGZILLA_BUG % 854925),
            log_function=self.err.warning,
            compat_type="error")

        yield self.get_test(
            r"\bcreateStorage\b",
            "The createStorage function in nsIDOMStorage now expects a window "
            "as its first argument.",
            "The createStorage function in nsIDOMStorage now expects a window "
            "as its first argument. See {bug}#c43 for more "
            "information.".format(bug=BUGZILLA_BUG % 660237),
            log_function=self.err.warning,
            compat_type="error")


@register_generator
class Gecko35RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 35 updates."""

    VERSION = FX36_DEFINITION

    def tests(self):
        box_object_subject = ("All interfaces derived from nsIBoxObject no "
                              "longer exist.")
        yield self.get_test(
            r"\bnsI\w*BoxObject\b",
            box_object_subject,
            box_object_subject + " If you use them with "
            "QueryInterface it's likely you just need to remove "
            "the function call. See %s for more information."
            % BUGZILLA_BUG % 979835,
            log_function=self.err.warning,
            compat_type="error")

        iterator_link = (MDN_DOC % "Web/JavaScript/Reference/Global_Objects"
                                   "/String/@@iterator")
        yield self.get_test(
            """['"]@@iterator['"]""",
            "The syntax for @@iterator has changed.",
            "The syntax for @@iterator has changed. See {link} for more "
            "information.".format(link=iterator_link),
            log_function=self.err.warning,
            compat_type="error")


#############################
#  Thunderbird Regex Tests  #
#############################

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
                    "Thunderbird 7. See %s for details." %
                        MDN_DOC % "Thunderbird_7_for_developers",
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
        js_patterns.update(dict((r"(\b|\()" + k, v) for k, v in prefix_patterns.items()))

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use",
                    "A javascript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 15." % pattern,
                    compat_type="error", log_function=self.err.notice)


@register_generator
class Thunderbird16RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 16 update."""

    VERSION = TB16_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"(contact|home|other|phone|work)\.heading": 762508,
                    r"mapItButton\.label": 762508,
                    r"mapIt\.tooltip": 762508,
                    r"font\.langGroup\.unicode": 323747,
                    r"offlineCompact\.(label|accesskey)": 758803,
                    r"mb\.label": 758804}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 16." % pattern,
                    compat_type="error")

        js_patterns = {r"(\b|\()parseAdoptedMsgLine": 740453,
                       r"(\b|\()normalEndMsgWriteStream": 740453}

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 16." % pattern,
                    compat_type="error", log_function=self.err.notice)

@register_generator
class Thunderbird17RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 17 update."""

    VERSION = TB17_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"searchTermListButtonsFlexValue": 743974,
                    r"sendWindow\.title": 255050,
                    r"addonsMgr\.label": 513164,
                    r"manageAddons(DescWin|DescUnix2)?\.(label|accesskey)": 513164}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 17." % pattern,
                    compat_type="error")

        js_patterns = {r"(\b|\()onlineContacts": 775105,
                       r"(\b|\()initContactList": 775105,
                       r"(\b|\()onShowAttachmentListContextMenu": 780200,
                       r"(\b|\()FillAttachmentListPopup": 780200,
                       r"(\b|\()showAddonsMgr": 513164,
                       r"(\b|\()(Get|Change)FeedOpenHandler": 596234,
                       r"(\b|\()gShowFeedSummaryToggle": 596234,
                       r"(\b|\()ChangeFeedShowSummaryPref": 596234,
                       r"(\b|\()FeedSetContentView(Toggle)?": 596234,
                       r"(\b|\()FeedCheckContentFormat": 596234}

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 17." % pattern,
                    compat_type="error", log_function=self.err.notice)

@register_generator
class Thunderbird18RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 18 update."""

    VERSION = TB18_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"fullZoomEnlargeCmd\.label": 738194,
                    r"fullZoomReduceCmd\.label": 738194,
                    r"fullZoomResetCmd\.label": 738194,
                    r"fullZoomToggleCmd\.label": 738194,
                    r"identitiesListDesc\.label": 314806,
                    r"connection\.error\.certError": 792046,
                    r"command\.wallops": 799068,
                    r"searchTermsInvalidMessage": 561762,
                    r"alreadyDefaultClientTitle": 595723,
                    r"alreadyDefault": 595723,
                    r"directoryUsedByOtherAccount": 577775}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 18." % pattern,
                    compat_type="error")

        js_patterns = {r"initContactList": 775105,
                       r"ircChannel\.prototype\.setMode": 799068,
                       r"SetUpToolbarButtons": 785980,
                       r"queryISupportsArray": 679696,
                       r"gAttachmentNotifier\.EditAction": 792979,
                       r"accountManagerContractID": 776705,
                       r"updateMoveTargetMode": 725488,
                       r"updatePurgeSpam": 725488,
                       r"gServer": 577775}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = (dict((r"(\b|\()" + k, v) for k, v in js_patterns.items()))

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 18." % pattern,
                    compat_type="error", log_function=self.err.notice)

@register_generator
class Thunderbird19RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 19 update."""

    VERSION = TB19_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"contextDesc\.accesskey": 775665,
                    r"contextIncoming\.label": 775665,
                    r"contextBoth\.label": 775665,
                    r"contextPostPlugin\.label": 775665,
                    r"contextPostPluginBoth\.label": 775665,
                    r"checkNow\.label": 804001,
                    r"checkNow\.acesskey": 804001,
                    r"outputFormatMenu\.label": 339887,
                    r"deliveryFormatMenu\.accesskey": 339887,
                    r"12564": 801383,
                    r"mime_multipartSignedBlurb": 800877,
                    r"command\.mode": 812921,
                    r"message\.mode": 812921}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 19." % pattern,
                    compat_type="error")

        js_patterns = {r"toggleFilter": 783491,
                       r"gFilterContext": 775665,
                       r"determineFilterType": 775665,
                       r"KEY_ISP_DIRECTORY_LIST": 793599,
                       r"disableEditableFields": 271730,
                       r"enableEditableFields": 271730,
                       r"gSmtpHostNameIsIllegal": 80855,
                       r"hostnameIsIllegal": 80855,
                       r"gLastPurpleConvId": 812921}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = (dict((r"(\b|\()" + k, v) for k, v in js_patterns.items()))

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 19." % pattern,
                    compat_type="error", log_function=self.err.notice)

@register_generator
class Thunderbird20RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 20 update."""

    VERSION = TB20_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"appmenuButton.tooltip": 812630,
                    r"decreaseFontSize.key": 813295,
                    r"decreaseFontSize.key2": 813295,
                    r"increaseFontSize.key": 813295,
                    r"increaseFontSize.key2": 813295,
                    r"serverNameEmpty": 327812,
                    r"confirmDeferAccount": 734034}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 20." % pattern,
                    compat_type="error")

        js_patterns = {r"gIdentity": 807101,
                       r"enabling": 807101,
                       r"cleanUpHostname": 327812,
                       r"gIOService": 794909,
                       r"gPromptService": 794909,
                       r"gIsOffline": 794909,
                       r"gIOService": 794909,
                       r"gPrefBranch": 795152,
                       r"GetWindowByWindowType": 795152,
                       r"specialTabs\.getApplicationUpgradeVersions": 795152,
                       r"specialTabs\.shouldShowTelemetryNotification": 795152,
                       r"specialTabs\.showTelemetryNotification": 795152,
                       r"specialTabs\.shouldShowAboutRightsNotification": 795152,
                       r"specialTabs\.showAboutRightsNotification": 795152,
                       r"gAttachmentNotifier\.handleMutations": 823009}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = (dict((r"(\b|\()" + k, v) for k, v in js_patterns.items()))

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 20." % pattern,
                    compat_type="error", log_function=self.err.notice)

@register_generator
class Thunderbird21RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 21 update."""

    VERSION = TB21_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"command\.whois": 842183}
        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 21." % pattern,
                    compat_type="error")

        js_patterns = {r"addEditorClickEventListener": 827017,
                       r"GetIOService": 795158,
                       r"GetPromptService": 795158,
                       r"GetLoginManager": 795158,
                       r"hasOnlyWhitespaces": 824150}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = dict((r"(\b|\()" + k, v) for k, v in js_patterns.items())

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 21." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird22RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 22 update."""

    VERSION = TB22_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"growlNotification": 852461,
                    r"5061": 448624,
                    r"ErrorCanNotEncrypt": 465351,
                    r"ErrorCanNotSign": 465351,
                    r"openFeedMessage\.label": 599036,
                    r"openFeedMessage\.accesskey": 599036,
                    r"openFeedWebPageInWindow\.label": 599036,
                    r"openFeedWebPageInWindow\.accesskey": 599036,
                    r"openFeedSummaryInWindow\.label": 599036,
                    r"openFeedSummaryInWindow\.accesskey": 599036,
                    r"color\.label": 845807,
                    r"color\.accesskey": 845807,
                    r"colors\.label": 845807,
                    r"overrideColors\.label": 845807,
                    r"fontsAndColors\.label": 845807,
                    r"fileHereMenu\.label": 325777,
                    r"fileHereMenu\.accesskey": 325777,
                    r"fileButton\.label": 325777,
                    r"fileButton\.accesskey": 325777}

        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 21." % pattern,
                    compat_type="error")

        js_patterns = {r"gMailSession": 765074,
                       r"gAccountManager": 852690,
                       r"gMimeHeaderParser": 852690,
                       r"InitAppEditMessagesMenu": 814956}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = dict((r"(\b|\()" + k, v) for k, v in js_patterns.items())

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 22." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird23RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 23 update."""

    VERSION = TB23_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"openAttachmentCmd\.label": 853135,
                    r"openAttachmentCmd\.accesskey": 853135,
                    r"applyToCollapsedMsgsTitle": 308690,
                    r"applyToCollapsedMsgs": 308690,
                    r"applyToCollapsedAlwaysAskCheckbox": 308690,
                    r"applyNowButton": 308690,
                    r"getNextNMessages": 595104,
                    r"openWindowWarningText": 595104,
                    r"sanitizePrefs2\.title": 807699,
                    r"sanitizeItems\.label": 807699,
                    r"clearDataSettings2\.label": 807699,
                    r"clearTimeDuration\.dateColumn": 807699,
                    r"clearTimeDuration\.nameColumn": 807699,
                    r"historySection\.label": 807699,
                    r"dataSection\.label": 807699,
                    r"column\.width": 807699}

        for pattern, bug in patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 21." % pattern,
                    compat_type="error")

        yield self.get_test_bug(
                252423, r"(\b|\()FinishHTMLSource",
                "Removed, renamed, or changed methods in use.",
                "A JavaScript function matched the pattern `FinishHTMLSource`, which has "
                "been flagged as having changed, removed, or deprecated "
                "in Thunderbird 23.",
                compat_type="error")


@register_generator
class Thunderbird24RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 24 update."""

    VERSION = TB24_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"contextForwardAsAttachment\.label": 508250,
                    r"contextForwardAsAttachment\.accesskey": 508250,
                    r"globalInbox\.label": 389139,
                    r"globalInbox\.accesskey": 389139,
                    r"toField3\.label": 686427,
                    r"fromField3\.label": 686427,
                    r"senderField3\.label": 686427,
                    r"organizationField3\.label": 686427,
                    r"replyToField3\.label": 686427,
                    r"subjectField3\.label": 686427,
                    r"ccField3\.label": 686427,
                    r"bccField3\.label": 686427,
                    r"newsgroupsField3\.label": 686427,
                    r"followupToField3\.label": 686427,
                    r"tagsHdr3\.label": 686427,
                    r"dateField3\.label": 686427,
                    r"userAgentField3\.label": 686427,
                    r"referencesField3\.label": 686427,
                    r"messageIdField3\.label": 686427,
                    r"inReplyToField3\.label": 686427,
                    r"originalWebsite3\.label": 686427,
                    r"folderContextOpenNewWindow\.label": 878933,
                    r"folderContextOpenNewWindow\.accesskey": 878933,
                    r"contextKillSubthreadMenu\.accesskey": 179033,
                    r"contextWatchThreadMenu\.accesskey": 179033,
                    r"viewCRLs\.label": 892255,
                    r"viewCRLs\.accesskey": 892255,
                    r"confirmMsgDelete\.shiftDel\.desc": 883485,
                    r"Nmessages": 179033}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 24." % pattern,
                    compat_type="error")

        js_patterns = {r"AlertWithTitle": 839279,
                       r"IsWhitespace": 839279,
                       r"IsEventHandler": 839279,
                       r"GetHTTPEquivMetaElement": 839279,
                       r"CreateHTTPEquivMetaElement": 839279,
                       r"CreateHTTPEquivElement": 839279,
                       r"ArrangeAccountCentralItems": 861767,
                       r"getInterfaceForType": 861767,
                       r"kHighestPort": 810680,
                       r"selectFolder": 878604,
                       r"updateSearchFolderPicker": 878604,
                       r"onChooseFolder": 878604,
                       r"updateInboxAccount": 389139,
                       r"gSelectionSummaryStrings\.Nmessages": 179033}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = dict((r"(\b|\()" + k, v) for k, v in js_patterns.items())

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 24." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird25RegexTests(CompatRegexTestHelper):
    """Regex tests for the Thunderbird 25 update."""

    VERSION = TB25_DEFINITION

    def tests(self):
        """String and JS changes for Thunderbird add-ons"""

        # String changes for add-ons that use our localizations.
        patterns = {r"getMsgButton\.label": 217941,
                    r"\b5000\b": 551919,
                    r"\b5001\b": 551919,
                    r"\b5002\b": 551919,
                    r"\b5003\b": 551919,
                    r"\b5004\b": 551919,
                    r"\b5005\b": 551919,
                    r"\b5006\b": 551919,
                    r"\b5007\b": 551919,
                    r"\b5008\b": 551919,
                    r"\b5009\b": 551919,
                    r"\b5010\b": 551919,
                    r"\b5011\b": 551919,
                    r"\b5012\b": 551919,
                    r"\b5013\b": 551919,
                    r"\b5014\b": 551919,
                    r"\b5015\b": 551919,
                    r"\b5029\b": 551919,
                    r"\b5030\b": 551919,
                    r"\b5031\b": 551919,
                    r"\b5032\b": 551919,
                    r"\b5036\b": 551919,
                    r"\b5037\b": 551919,
                    r"\b5038\b": 551919,
                    r"\b5039\b": 551919,
                    r"\b5040\b": 551919,
                    r"\b5041\b": 551919,
                    r"\b5042\b": 551919,
                    r"\b5043\b": 551919,
                    r"\b5045\b": 551919,
                    r"\b5046\b": 551919,
                    r"\b5047\b": 551919,
                    r"\b5048\b": 551919,
                    r"\b5049\b": 551919,
                    r"\b5050\b": 551919,
                    r"\b5051\b": 551919,
                    r"\b5052\b": 551919,
                    r"\b5053\b": 551919,
                    r"\b5054\b": 551919,
                    r"\b5056\b": 551919,
                    r"\b5057\b": 551919,
                    r"\b5065\b": 551919,
                    r"\b5066\b": 551919,
                    r"\b5067\b": 551919,
                    r"\b5068\b": 551919,
                    r"\b5069\b": 551919,
                    r"\b5070\b": 551919,
                    r"\b5071\b": 551919,
                    r"\b5072\b": 551919,
                    r"\b5073\b": 551919,
                    r"\b5074\b": 551919,
                    r"\b5075\b": 551919,
                    r"\b5076\b": 551919,
                    r"\b5077\b": 551919,
                    r"\b5078\b": 551919,
                    r"\b5079\b": 551919,
                    r"\b5080\b": 551919,
                    r"\b5081\b": 551919,
                    r"\b5082\b": 551919,
                    r"\b5084\b": 551919,
                    r"\b5085\b": 551919,
                    r"\b5090\b": 551919,
                    r"\b5092\b": 551919,
                    r"\b5093\b": 551919,
                    r"\b5095\b": 551919,
                    r"\b5096\b": 551919,
                    r"\b5097\b": 551919,
                    r"\b5100\b": 551919,
                    r"\b5103\b": 551919,
                    r"\b5105\b": 551919,
                    r"\b5106\b": 551919,
                    r"\b5107\b": 551919,
                    r"\b5108\b": 551919,
                    r"\b5110\b": 551919,
                    r"\b5111\b": 551919,
                    r"\b5112\b": 551919,
                    r"\b5113\b": 551919,
                    r"\b5114\b": 551919,
                    r"\b5115\b": 551919,
                    r"\b5116\b": 551919,
                    r"\b5117\b": 551919,
                    r"\b5118\b": 551919,
                    r"\b5119\b": 551919,
                    r"pop3PasswordFailure": 221592}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having changed in Thunderbird 25." % pattern,
                    compat_type="error")

        js_patterns = {r"AddFileAttachment": 889031,
                       r"AddUrlAttachment": 889031,
                       r"gQuickSearchFocusEl": 452232,
                       r"gIsOffline": 452232,
                       r"gSessionAdded": 452232,
                       r"gCurrentAutocompleteDirectory": 452232,
                       r"gAutocompleteSession": 452232,
                       r"gSetupLdapAutocomplete": 452232,
                       r"gLDAPSession": 452232,
                       r"setupLdapAutocompleteSession": 452232,
                       r"directoryServerObserver": 452232,
                       r"AddDirectoryServerObserver": 452232,
                       r"RemoveDirectoryServerObserver": 452232,
                       r"AddDirectorySettingsObserver": 452232,
                       r"RemoveDirectorySettingsObserver": 452232,
                       r"ReleaseAutoCompleteState": 452232}

        # Add restricting prefix for ( or word boundary to prevent substring matching.
        js_patterns = dict((r"(\b|\()" + k, v) for k, v in js_patterns.items())

        for pattern, bug in js_patterns.items():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed, renamed, or changed methods in use.",
                    "A JavaScript function matched the pattern `%s`, which has "
                    "been flagged as having changed, removed, or deprecated "
                    "in Thunderbird 25." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird26RegexTests(CompatRegexTestHelper):

    VERSION = TB26_DEFINITION
    BUG_ID = 889022

    def tests(self):
        """Regex tests for the Thunderbird 26 update."""
        yield self.get_test_bug(
            self.BUG_ID, r"chrome://messenger/content/widgetglue\.js",
            "The file `widgetglue.js` has been removed.",
            "The file `widgetglue.js` has been removed. See %s for more "
            "information." % BUGZILLA_BUG % self.BUG_ID,
            compat_type="error", log_function=self.err.warning)

        """String changes for Thunderbird 26 update."""
        patterns = {r"pop3MessageFolderBusy": 592235}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed property in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed in Thunderbird 26." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird27RegexTests(CompatRegexTestHelper):

    VERSION = TB27_DEFINITION

    def tests(self):
        """String changes for Thunderbird 27 update."""
        patterns = {r"folderCharsetTab\.label": 916823,
                    r"folderCharsetTab\.accesskey": 916823,
                    r"folderCharsetOverride\.label": 916823,
                    r"folderCharsetOverride\.accesskey": 916823,
                    r"appmenuQFBMenu\.label": 928670,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed in Thunderbird 27." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird28RegexTests(CompatRegexTestHelper):

    VERSION = TB28_DEFINITION

    def tests(self):
        """String changes for Thunderbird 28 update."""
        patterns = {r"junkBarMessage2\.label": 562048,
                    r"junkBarButton1\.label": 562048,
                    r"junkInfoButton\.label": 562048,
                    r"remoteContentMessage2\.label": 562048,
                    r"loadRemoteContentButton3\.label": 562048,
                    r"phishingBarMessage2\.label": 562048,
                    r"removePhishingBarButton1\.label": 562048,
                    r"disablePhishingWarning1\.label": 562048,
                    r"reportPhishingError1\.label": 562048,
                    r"mdnBarIgnoreButton2\.label": 562048,
                    r"mdnBarIgnoreButton2\.accesskey": 562048,
                    r"mdnBarSendButton2\.label": 562048,
                    r"mdnBarSendButton2\.accesskey": 562048,
                    r"editMessageDescription\.label": 939982,
                    r"editMessageButton\.label": 939982,
                    r"downloadMessagesNow": 924876,
                    r"sendMessagesNow": 924876,
                    r"processMessagesLater": 924876,
                    r"accountExists": 40012,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed or renamed "
                    "in Thunderbird 28." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird29RegexTests(CompatRegexTestHelper):

    VERSION = TB29_DEFINITION

    def tests(self):
        """String changes for Thunderbird 29 update."""
        patterns = {r"update\.checkingAddonCompat": 707489,
                    r"columnChooser\.tooltip": 881073,
                    r"threadColumn\.tooltip": 881073,
                    r"fromColumn\.tooltip": 881073,
                    r"recipientColumn\.tooltip": 881073,
                    r"attachmentColumn\.tooltip": 881073,
                    r"subjectColumn\.tooltip": 881073,
                    r"dateColumn\.tooltip": 881073,
                    r"priorityColumn\.tooltip": 881073,
                    r"tagsColumn\.tooltip": 881073,
                    r"accountColumn\.tooltip": 881073,
                    r"statusColumn\.tooltip": 881073,
                    r"sizeColumn\.tooltip": 881073,
                    r"junkStatusColumn\.tooltip": 881073,
                    r"unreadColumn\.tooltip": 881073,
                    r"totalColumn\.tooltip": 881073,
                    r"readColumn\.tooltip": 881073,
                    r"receivedColumn\.tooltip": 881073,
                    r"flagColumn\.tooltip": 881073,
                    r"starredColumn\.tooltip": 881073,
                    r"locationColumn\.tooltip": 881073,
                    r"idColumn\.tooltip": 881073,
                    r"phishingOptionDisableDetection\.label": 926473,
                    r"phishingOptionDisableDetection\.accesskey": 926473,
                    r"contextEditAsNew\.label": 956481,
                    r"contextEditAsNew\.accesskey": 956481,
                    r"EditContact\.label": 956481,
                    r"EditContact\.accesskey": 956481,
                    r"choosethisnewsserver\.label": 878805,
                    r"moveHereMenu\.label": 878805,
                    r"moveHereMenu\.accesskey": 878805,
                    r"newfolderchoosethis\.label": 878805,
                    r"thisFolder\.label": 878805,
                    r"thisFolder\.accesskey": 878805,
                    r"fileHereMenu\.label": 878805,
                    r"fileHereMenu\.accesskey": 878805,
                    r"copyHereMenu\.label": 878805,
                    r"copyHereMenu\.accesskey": 878805,
                    r"autoCheck\.label": 958850,
                    r"enableAppUpdate\.label": 958850,
                    r"enableAppUpdate\.accesskey": 958850,
                    r"enableAddonsUpdate\.label": 958850,
                    r"enableAddonsUpdate\.accesskey": 958850,
                    r"whenUpdatesFound\.label": 958850,
                    r"modeAskMe\.label": 958850,
                    r"modeAskMe\.accesskey": 958850,
                    r"modeAutomatic\.label": 958850,
                    r"modeAutomatic\.accesskey": 958850,
                    r"modeAutoAddonWarn\.label": 958850,
                    r"modeAutoAddonWarn\.accesskey": 958850,
                    r"showUpdates\.label": 958850,
                    r"showUpdates\.accesskey": 958850,
                    r"update\.checkInsideButton\.label": 707489,
                    r"update\.checkInsideButton\.accesskey": 707489,
                    r"update\.resumeButton\.label": 707489,
                    r"update\.resumeButton\.accesskey": 707489,
                    r"update\.openUpdateUI\.applyButton\.label": 707489,
                    r"update\.openUpdateUI\.applyButton\.accesskey": 707489,
                    r"update\.restart\.updateButton\.label": 707489,
                    r"update\.restart\.updateButton\.accesskey": 707489,
                    r"update\.restart\.restartButton\.label": 707489,
                    r"update\.restart\.restartButton\.accesskey": 707489,
                    r"update\.openUpdateUI\.upgradeButton\.label": 707489,
                    r"update\.openUpdateUI\.upgradeButton\.accesskey": 707489,
                    r"update\.restart\.upgradeButton\.label": 707489,
                    r"update\.restart\.upgradeButton\.accesskey": 707489,
                    r"command\.invite": 920801,
                    r"ctcp\.ping": 957918,
                    r"vkontakte\.usernameHint": 957918,
                    r"dateformat": 544315,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed or renamed "
                    "in Thunderbird 29." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird30RegexTests(CompatRegexTestHelper):

    VERSION = TB30_DEFINITION

    def tests(self):
        """String changes for Thunderbird 30 update."""
        patterns = {r"log\.lastWeek": 863226,
                    r"log\.twoWeeksAgo": 863226,
                    r"filemessageschoosethis\.label": 964425,
                    r"recentfolders\.label": 964425,
                    r"protocolNotFound\.title": 973368,
                    r"protocolNotFound\.longDesc": 973368,
                    r"quickFilterBar\.barLabel\.label": 592248,
                    r"updateOthers\.label": 978563,
                    r"enableAddonsUpdate3\.label": 978563,
                    r"enableAddonsUpdate3\.accesskey": 978563,
                    r"bounceSystemDockIcon\.label": 601263,
                    r"bounceSystemDockIcon\.accesskey": 601263,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed or renamed "
                    "in Thunderbird 30." % pattern,
                    compat_type="error")

@register_generator
class Thunderbird31RegexTests(CompatRegexTestHelper):

    VERSION = TB31_DEFINITION

    def tests(self):
        """String changes for Thunderbird 31 update."""
        patterns = {r"youSendItMgmt\.viewSettings": 894306,
                    r"youSendItSettings\.username": 894306,
                    r"youSendItMgmt\.needAnAccount": 894306,
                    r"youSendItMgmt\.learnMore": 894306,
                    r"preferencesCmd\.label": 992643,
                    r"preferencesCmd\.accesskey": 992643,
                    r"proxy\.label": 992643,
                    r"proxy\.accesskey": 992643,
                    r"folderPropsCmd\.label": 992643,
                    r"folderPropsFolderCmd\.label": 992643,
                    r"folderPropsNewsgroupCmd\.label": 992643,
                    r"filtersCmd\.label": 992643,
                    r"filtersCmd\.accesskey": 992643,
                    r"accountManagerCmd\.accesskey": 992643,
                    r"accountManagerCmdUnix\.accesskey": 992643,
                    r"accountManagerCmd\.label": 992643,
                    r"accountManagerCmd\.accesskey": 992643,
                    r"accountManagerCmdUnix\.accesskey": 992643,
                    r"preferencesCmd\.label": 992643,
                    r"preferencesCmd\.accesskey": 992643,
                    r"preferencesCmdUnix\.label": 992643,
                    r"preferencesCmdUnix\.accesskey": 992643,
                    r"findCmd\.label": 530629,
                    r"findCmd\.key": 530629,
                    r"findCmd\.accesskey": 530629,
                    r"ubuntuOneMgmt\.viewSettings": 991220,
                    r"UbuntuOneSettings\.emailAddress": 991220,
                    r"UbuntuOneSettings\.needAnAccount": 991220,
                    r"UbuntuOneSettings\.learnMore": 991220,
                    r"propertiesCmd\.label": 992643,
                    r"propertiesCmd\.accesskey": 992643,
                    r"settingsOfflineCmd\.label": 992643,
                    r"settingsOfflineCmd\.accesskey": 992643,
                    r"folderContextProperties\.label": 992643,
                    r"folderContextProperties\.accesskey": 992643,
                    r"folderContextSettings\.label": 992643,
                    r"folderContextSettings\.accesskey": 992643,
                    r"itemCookies\.label": 953426,
                    r"cookies\.intro": 953426,
                    r"doNotTrack\.label": 953426,
                    r"doNotTrack\.accesskey": 953426,
                    r"allowRemoteContent1\.label": 457296,
                    r"allowRemoteContent1\.accesskey": 457296,
                    r"allowRemoteContent1\.tooltip": 457296,
                    r"remoteContentOptionAllowForAddress\.label": 457296,
                    r"remoteContentOptionAllowForAddress\.accesskey": 457296,
                    r"\b12504\b": 802266,
                    r"\b12505\b": 802266,
                    r"\b12507\b": 802266,
                    r"\b12522\b": 802266,
                    r"\b12508\b": 802266,
                    r"\b12509\b": 802266,
                    r"\b12521\b": 802266,
                    r"\b12523\b": 802266,
                    r"\b12533\b": 802266,
                    r"\b12534\b": 802266,
                    r"\b12535\b": 802266,
                    r"\b12536\b": 802266,
                    r"\b12537\b": 802266,
                    r"\b12538\b": 802266,
                    r"\b12539\b": 802266,
                    r"\b12540\b": 802266,
                    r"\b12541\b": 802266,
                    r"\b12550\b": 802266,
                    r"\b12551\b": 802266,
                    r"\b12556\b": 802266,
                    r"\b12557\b": 802266,
                    r"\b12558\b": 802266,
                    r"\b12559\b": 802266,
                    r"\b12562\b": 802266,
                    r"\b12566\b": 802266,
                    r"tooltip\.idleTime": 987577,
                    r"receivingMsgs": 86233,
                    r"hostContacted": 86233,
                    r"noMessages": 86233,
                    r"receivedMessages": 86233,
                    r"mailnews\.reply_header_authorwrote": 995797,
                    r"mailnews\.reply_header_ondate": 995797,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    "Removed labels in use.",
                    "Some string matched the pattern `%s`, which has been "
                    "flagged as having been removed or renamed "
                    "in Thunderbird 31." % pattern,
                    compat_type="error")
