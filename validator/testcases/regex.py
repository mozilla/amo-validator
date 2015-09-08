import re
from functools import wraps

from validator.compat import (
    FX38_DEFINITION, FX39_DEFINITION, FX40_DEFINITION, FX41_DEFINITION,
    TB29_DEFINITION, TB30_DEFINITION, TB31_DEFINITION)
from validator.constants import BUGZILLA_BUG, MDN_DOC
from validator.contextgenerator import ContextGenerator
from .chromemanifest import DANGEROUS_CATEGORIES, DANGEROUS_CATEGORY_WARNING
from .javascript.predefinedentities import (BANNED_PREF_BRANCHES,
                                            BANNED_PREF_REGEXPS,
                                            MARIONETTE_MESSAGE)


registered_regex_tests = []


NP_WARNING = 'Network preferences may not be modified.'
EUP_WARNING = 'Extension update settings may not be modified.'
NSINHS_LINK = MDN_DOC % 'XPCOM_Interface_Reference/nsINavHistoryService'


def run_regex_tests(document, err, filename, context=None, is_js=False,
                    explicit=False):
    """Run all of the regex-based JS tests."""

    # When `explicit` is true, only run tests which explicitly
    # specify which files they're applicable to.

    if context is None:
        context = ContextGenerator(document)

    # Run all of the registered tests.
    for cls in registered_regex_tests:
        if not hasattr(cls, 'applicable'):
            if explicit:
                continue
        else:
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


def merge_description(base, description):
    base = base.copy()
    if isinstance(description, dict):
        base.update(description)
    else:
        base['description'] = description
    return base


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
                kw = {'err_id': ('testcases_regex', 'generic', '_generated'),
                      log_function.__name__: title,
                      'filename': self.filename,
                      'line': self.context.get_line(match.start()),
                      'context': self.context,
                      'compatibility_type': compat_type,
                      'for_appversions': app_versions,
                      'tier': self.err.tier if app_versions is None else 5}

                log_function(**merge_description(kw, message))
                matched = True
            return matched

        return wrapper

    def get_test_bug(self, bug, pattern, title, message, **kwargs):
        """Helper function to mix in a bug number."""
        message = [message,
                   'See bug %s for more information.' % BUGZILLA_BUG % bug]
        return self.get_test(pattern, title, message, **kwargs)


@register_generator
class GenericRegexTests(RegexTestGenerator):
    """Test for generic, banned patterns in a document being scanned."""

    def tests(self):
        # globalStorage.(.+)password test removed for bug 752740

        yield self.get_test(
                r'resource://services-sync',
                'Sync services objects are not intended to be re-used',
                'The Sync services objects are not intended to be re-used, and '
                'they often change in ways that break add-ons. It is strongly '
                'recommended that you do not rely on them.')

    def js_tests(self):
        yield self.get_test(
                'mouse(move|over|out)',
                'Mouse events may cause performance issues.',
                'The use of `mousemove`, `mouseover`, and `mouseout` is '
                'discouraged. These events are dispatched with high frequency '
                'and can cause severe performance issues.',
                log_function=self.err.warning)


@register_generator
class DOMMutationRegexTests(RegexTestGenerator):
    """
    These regex tests will test that DOM mutation events are not used. These
    events have extreme performance penalties associated with them and are
    currently deprecated.

    Added from bug 642153
    """

    EVENTS = ('DOMAttrModified', 'DOMAttributeNameChanged',
              'DOMCharacterDataModified', 'DOMElementNameChanged',
              'DOMNodeInserted', 'DOMNodeInsertedIntoDocument',
              'DOMNodeRemoved', 'DOMNodeRemovedFromDocument',
              'DOMSubtreeModified', )

    def js_tests(self):
        for event in self.EVENTS:
            yield self.get_test(
                    event,
                    'DOM mutation event use prohibited',
                    'DOM mutation events are flagged because of their '
                    'deprecated status as well as their extreme inefficiency. '
                    'Consider using a different event.')


@register_generator
class NewTabRegexTests(RegexTestGenerator):
    """
    Attempts to code using roundabout methods of overriding the new tab page.
    """

    PATTERN = r"""
        (?x)
        == \s* ["']about:(newtab|blank)["'] |
        ["']about:(newtab|blank)["'] \s* == |
        /\^?about:newtab\$?/ \s* \. test\b |
        \?what=newtab
    """

    def tests(self):
        yield self.get_test(
            self.PATTERN,
            'Possible attempt to override new tab page',
            {'description': (
                'The new tab page should be changed only by writing '
                'to the appropriate preference in the default preferences '
                'branch. Such changes may only be made after an explicit '
                'user opt-in, unless the add-on was explicitly and directly '
                'installed by the user, and changing the new tab page is its '
                'primary purpose.',
                'If this code does not change the behavior of the new tab '
                'page, it may be ignored.'),
             'signing_help':
                'Extensions may not programmatically override the new tab '
                'page. If this code has another purpose, we nonetheless '
                'recommend against testing URLs for these values, since '
                'results can be unpredictable, and better options usually '
                'exist. If you cannot avoid making these tests, please leave '
                'this code unchanged, and it will be ignored in future '
                'submissions.',
             'signing_severity': 'low'})


@register_generator
class UnsafeTemplateRegexTests(RegexTestGenerator):
    """
    Checks for the use of unsafe template escape sequences.
    """

    @classmethod
    def applicable(cls, err, filename, document):
        # Perhaps this should just run on all non-binary files, but
        # we'll try to be more selective for the moment.
        return bool(re.match(r'.*\.(js(|m)|hbs|handlebars|mustache|'
                             r'(t|)htm(|l)|tm?pl)',
                             filename))

    def tests(self):
        for unsafe, safe in (('<%=', '<%-'),
                             ('{{{', '{{'),
                             ('ng-bind-html-unsafe=', 'ng-bind-html')):
            yield self.get_test(
                    re.escape(unsafe),
                    'Potentially unsafe template escape sequence',
                    'The use of non-HTML-escaping template escape sequences is '
                    'potentially dangerous and highly discouraged. Non-escaped '
                    'HTML may only be used when properly sanitized, and in most '
                    'cases safer escape sequences such as `%s` must be used '
                    'instead.' % safe)


@register_generator
class JSPrototypeExtRegexTests(RegexTestGenerator):
    """
    These regex tests will ensure that the developer is not modifying the
    prototypes of the global JS types.

    Added from bug 696172
    """

    @classmethod
    def applicable(cls, err, filename, document):
        return not (filename.endswith('.jsm') or 'EXPORTED_SYMBOLS' in document)

    def js_tests(self):
        yield self.get_test(
                r'\b(String|Object|Number|Date|RegExp|Function|Boolean|Array|'
                r'Iterator)\.prototype(\.[a-zA-Z0-9]+|\[.+\])\s*=',
                'JS prototype extension',
                'It appears that an extension of a built-in JS type was made. '
                'This is not allowed for security and compatibility reasons.',
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


DEP_INTERFACE = 'Deprecated interface in use'
DEP_INTERFACE_DESC = ('This add-on uses `%s`, which is deprecated in Gecko %d '
                      'and should not be used.')


@register_generator
class Gecko38RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 38 updates."""

    VERSION = FX38_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\bmozIndexedDB\b',
            'mozIndexedDB has been removed.',
            'mozIndexedDB has been removed. You should use indexedDB instead. '
            'See %s for more information.' % BUGZILLA_BUG % 975699,
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\b(nsICompositionStringSynthesizer|'
            r'sendCompositionEvent|'
            r'createCompositionStringSynthesizer)\b',
            'nsICompositionStringSynthesizer, sendCompositionEvent and '
            'createCompositionStringSynthesizer were removed.',
            'The nsICompositionStringSynthesizer interface and the '
            'sendCompositionEvent and createCompositionStringSynthesizer '
            'functions have been removed. See %s for more information.'
            % MDN_DOC
            % 'Mozilla/Tech/XPCOM/Reference/Interface/nsITextInputProcessor',
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\b(newChannel2|asyncFetch2)\b',
            'asyncFetch2 and newChannel2 are now deprecated.',
            'asyncFetch2 and newChannel2 are now deprecated. Use asyncFetch '
            'or newChannel instead. See %s for more information.'
            % BUGZILLA_BUG % 1125618,
            compat_type='warning')

        yield self.get_test(
            r'\b(onProxyAvailable|asyncResolve)\b',
            'The onProxyAvailable and asyncResolve functions have changed.',
            'The onProxyAvailable and asyncResolve functions have changed. '
            'They now take an nsIChannel instead of an nsIURI as an argument. '
            'See %s for more information.' % BUGZILLA_BUG % 436344,
            log_function=self.err.warning,
            compat_type='error')


@register_generator
class Gecko39RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 39 updates."""

    VERSION = FX39_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\b__noSuchMethod__\b',
            'The __noSuchMethod__ property has been deprecated.',
            'The __noSuchMethod__ property has been deprecated. See %s for '
            'more information.' % MDN_DOC
            % 'Web/JavaScript/Reference/Global_Objects/Object/noSuchMethod',
            log_function=self.err.warning,
            compat_type='warning')

        yield self.get_test(
            r'\bsendAsBinary\b',
            'The function sendAsBinary() in XMLHttpRequest has been removed.',
            'The function sendAsBinary() in XMLHttpRequest has been removed. '
            'You can use send() with a Blob instead. See %s for more '
            'information.' % BUGZILLA_BUG % 853162,
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\blightweightThemes\.(usedThemes|isThemeSelected)\b',
            'The preferences used to store theme selection have changed.',
            'The preferences used to store theme selection have changed. See '
            '%s for more information.' % (BUGZILLA_BUG % 1094821 + '#c39'),
            log_function=self.err.warning,
            compat_type='error')


@register_generator
class Gecko40RegexTests(CompatRegexTestHelper):
    """Regex tests for Gecko 40 updates."""

    VERSION = FX40_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\b([gs]etKeywordForBookmark|getURIForKeyword)\b',
            'The old keywords API is deprecated.',
            'The old keywords API is deprecated. You should use '
            'PlacesUtils.keywords instead. See %s for more information.'
            % MDN_DOC % 'Mozilla/Tech/Places/Using_the_Places_keywords_API',
            log_function=self.err.warning,
            compat_type='warning')

        yield self.get_test(
            r'\b(fuelIApplication|extIApplication)\b',
            'The FUEL library is now deprecated.',
            'The FUEL library is now deprecated. You should use the add-ons '
            'SDK or Services.jsm. See %s for more information.'
            % MDN_DOC % 'Mozilla/Tech/Toolkit_API/FUEL',
            log_function=self.err.warning,
            compat_type='warning')

        yield self.get_test(
            r'\bresource://gre/modules/Dict.jsm\b',
            'The Dict.jsm module has been removed.',
            'The Dict.jsm module has been removed. You can use the native Map '
            'object instead. See %s for more information.'
            % MDN_DOC % 'Web/JavaScript/Reference/Global_Objects/Map',
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\bsessionstore-state-write\b',
            "The \"sessionstore-state-write\" notification has been removed.",
            "The \"sessionstore-state-write\" notification has been removed. "
            'See %s for more information.' % BUGZILLA_BUG % 1157235,
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\bnsISSLErrorListener\b',
            'The nsISSLErrorListener interface has been removed.',
            'The nsISSLErrorListener interface has been removed. See %s for '
            'more information.' % BUGZILLA_BUG % 844351,
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r"""require\(['"]sdk/widget['"]\)""",
            'The widget module has been removed.',
            'The widget module has been removed. You can use ActionButton or '
            'ToggleButton instead. See %s for more information.'
            % 'https://developer.mozilla.org/en-US/Add-ons/SDK/'
              'High-Level_APIs/widget',
            log_function=self.err.warning,
            compat_type='error')


#############################
#  Thunderbird Regex Tests  #
#############################


@register_generator
class Thunderbird29RegexTests(CompatRegexTestHelper):

    VERSION = TB29_DEFINITION

    def tests(self):
        """String changes for Thunderbird 29 update."""
        patterns = {r'update\.checkingAddonCompat': 707489,
                    r'columnChooser\.tooltip': 881073,
                    r'threadColumn\.tooltip': 881073,
                    r'fromColumn\.tooltip': 881073,
                    r'recipientColumn\.tooltip': 881073,
                    r'attachmentColumn\.tooltip': 881073,
                    r'subjectColumn\.tooltip': 881073,
                    r'dateColumn\.tooltip': 881073,
                    r'priorityColumn\.tooltip': 881073,
                    r'tagsColumn\.tooltip': 881073,
                    r'accountColumn\.tooltip': 881073,
                    r'statusColumn\.tooltip': 881073,
                    r'sizeColumn\.tooltip': 881073,
                    r'junkStatusColumn\.tooltip': 881073,
                    r'unreadColumn\.tooltip': 881073,
                    r'totalColumn\.tooltip': 881073,
                    r'readColumn\.tooltip': 881073,
                    r'receivedColumn\.tooltip': 881073,
                    r'flagColumn\.tooltip': 881073,
                    r'starredColumn\.tooltip': 881073,
                    r'locationColumn\.tooltip': 881073,
                    r'idColumn\.tooltip': 881073,
                    r'phishingOptionDisableDetection\.label': 926473,
                    r'phishingOptionDisableDetection\.accesskey': 926473,
                    r'contextEditAsNew\.label': 956481,
                    r'contextEditAsNew\.accesskey': 956481,
                    r'EditContact\.label': 956481,
                    r'EditContact\.accesskey': 956481,
                    r'choosethisnewsserver\.label': 878805,
                    r'moveHereMenu\.label': 878805,
                    r'moveHereMenu\.accesskey': 878805,
                    r'newfolderchoosethis\.label': 878805,
                    r'thisFolder\.label': 878805,
                    r'thisFolder\.accesskey': 878805,
                    r'fileHereMenu\.label': 878805,
                    r'fileHereMenu\.accesskey': 878805,
                    r'copyHereMenu\.label': 878805,
                    r'copyHereMenu\.accesskey': 878805,
                    r'autoCheck\.label': 958850,
                    r'enableAppUpdate\.label': 958850,
                    r'enableAppUpdate\.accesskey': 958850,
                    r'enableAddonsUpdate\.label': 958850,
                    r'enableAddonsUpdate\.accesskey': 958850,
                    r'whenUpdatesFound\.label': 958850,
                    r'modeAskMe\.label': 958850,
                    r'modeAskMe\.accesskey': 958850,
                    r'modeAutomatic\.label': 958850,
                    r'modeAutomatic\.accesskey': 958850,
                    r'modeAutoAddonWarn\.label': 958850,
                    r'modeAutoAddonWarn\.accesskey': 958850,
                    r'showUpdates\.label': 958850,
                    r'showUpdates\.accesskey': 958850,
                    r'update\.checkInsideButton\.label': 707489,
                    r'update\.checkInsideButton\.accesskey': 707489,
                    r'update\.resumeButton\.label': 707489,
                    r'update\.resumeButton\.accesskey': 707489,
                    r'update\.openUpdateUI\.applyButton\.label': 707489,
                    r'update\.openUpdateUI\.applyButton\.accesskey': 707489,
                    r'update\.restart\.updateButton\.label': 707489,
                    r'update\.restart\.updateButton\.accesskey': 707489,
                    r'update\.restart\.restartButton\.label': 707489,
                    r'update\.restart\.restartButton\.accesskey': 707489,
                    r'update\.openUpdateUI\.upgradeButton\.label': 707489,
                    r'update\.openUpdateUI\.upgradeButton\.accesskey': 707489,
                    r'update\.restart\.upgradeButton\.label': 707489,
                    r'update\.restart\.upgradeButton\.accesskey': 707489,
                    r'command\.invite': 920801,
                    r'ctcp\.ping': 957918,
                    r'vkontakte\.usernameHint': 957918,
                    r'dateformat': 544315,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    'Removed labels in use.',
                    'Some string matched the pattern `%s`, which has been '
                    'flagged as having been removed or renamed '
                    'in Thunderbird 29.' % pattern,
                    compat_type='error')

@register_generator
class Thunderbird30RegexTests(CompatRegexTestHelper):

    VERSION = TB30_DEFINITION

    def tests(self):
        """String changes for Thunderbird 30 update."""
        patterns = {r'log\.lastWeek': 863226,
                    r'log\.twoWeeksAgo': 863226,
                    r'filemessageschoosethis\.label': 964425,
                    r'recentfolders\.label': 964425,
                    r'protocolNotFound\.title': 973368,
                    r'protocolNotFound\.longDesc': 973368,
                    r'quickFilterBar\.barLabel\.label': 592248,
                    r'updateOthers\.label': 978563,
                    r'enableAddonsUpdate3\.label': 978563,
                    r'enableAddonsUpdate3\.accesskey': 978563,
                    r'bounceSystemDockIcon\.label': 601263,
                    r'bounceSystemDockIcon\.accesskey': 601263,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    'Removed labels in use.',
                    'Some string matched the pattern `%s`, which has been '
                    'flagged as having been removed or renamed '
                    'in Thunderbird 30.' % pattern,
                    compat_type='error')

@register_generator
class Thunderbird31RegexTests(CompatRegexTestHelper):

    VERSION = TB31_DEFINITION

    def tests(self):
        """String changes for Thunderbird 31 update."""
        patterns = {r'youSendItMgmt\.viewSettings': 894306,
                    r'youSendItSettings\.username': 894306,
                    r'youSendItMgmt\.needAnAccount': 894306,
                    r'youSendItMgmt\.learnMore': 894306,
                    r'preferencesCmd\.label': 992643,
                    r'preferencesCmd\.accesskey': 992643,
                    r'proxy\.label': 992643,
                    r'proxy\.accesskey': 992643,
                    r'folderPropsCmd\.label': 992643,
                    r'folderPropsFolderCmd\.label': 992643,
                    r'folderPropsNewsgroupCmd\.label': 992643,
                    r'filtersCmd\.label': 992643,
                    r'filtersCmd\.accesskey': 992643,
                    r'accountManagerCmd\.accesskey': 992643,
                    r'accountManagerCmdUnix\.accesskey': 992643,
                    r'accountManagerCmd\.label': 992643,
                    r'accountManagerCmd\.accesskey': 992643,
                    r'accountManagerCmdUnix\.accesskey': 992643,
                    r'preferencesCmd\.label': 992643,
                    r'preferencesCmd\.accesskey': 992643,
                    r'preferencesCmdUnix\.label': 992643,
                    r'preferencesCmdUnix\.accesskey': 992643,
                    r'findCmd\.label': 530629,
                    r'findCmd\.key': 530629,
                    r'findCmd\.accesskey': 530629,
                    r'ubuntuOneMgmt\.viewSettings': 991220,
                    r'UbuntuOneSettings\.emailAddress': 991220,
                    r'UbuntuOneSettings\.needAnAccount': 991220,
                    r'UbuntuOneSettings\.learnMore': 991220,
                    r'propertiesCmd\.label': 992643,
                    r'propertiesCmd\.accesskey': 992643,
                    r'settingsOfflineCmd\.label': 992643,
                    r'settingsOfflineCmd\.accesskey': 992643,
                    r'folderContextProperties\.label': 992643,
                    r'folderContextProperties\.accesskey': 992643,
                    r'folderContextSettings\.label': 992643,
                    r'folderContextSettings\.accesskey': 992643,
                    r'itemCookies\.label': 953426,
                    r'cookies\.intro': 953426,
                    r'doNotTrack\.label': 953426,
                    r'doNotTrack\.accesskey': 953426,
                    r'allowRemoteContent1\.label': 457296,
                    r'allowRemoteContent1\.accesskey': 457296,
                    r'allowRemoteContent1\.tooltip': 457296,
                    r'remoteContentOptionAllowForAddress\.label': 457296,
                    r'remoteContentOptionAllowForAddress\.accesskey': 457296,
                    r'\b12504\b': 802266,
                    r'\b12505\b': 802266,
                    r'\b12507\b': 802266,
                    r'\b12522\b': 802266,
                    r'\b12508\b': 802266,
                    r'\b12509\b': 802266,
                    r'\b12521\b': 802266,
                    r'\b12523\b': 802266,
                    r'\b12533\b': 802266,
                    r'\b12534\b': 802266,
                    r'\b12535\b': 802266,
                    r'\b12536\b': 802266,
                    r'\b12537\b': 802266,
                    r'\b12538\b': 802266,
                    r'\b12539\b': 802266,
                    r'\b12540\b': 802266,
                    r'\b12541\b': 802266,
                    r'\b12550\b': 802266,
                    r'\b12551\b': 802266,
                    r'\b12556\b': 802266,
                    r'\b12557\b': 802266,
                    r'\b12558\b': 802266,
                    r'\b12559\b': 802266,
                    r'\b12562\b': 802266,
                    r'\b12566\b': 802266,
                    r'tooltip\.idleTime': 987577,
                    r'receivingMsgs': 86233,
                    r'hostContacted': 86233,
                    r'noMessages': 86233,
                    r'receivedMessages': 86233,
                    r'mailnews\.reply_header_authorwrote': 995797,
                    r'mailnews\.reply_header_ondate': 995797,}

        for pattern, bug in patterns.iteritems():
            yield self.get_test_bug(
                    bug, pattern,
                    'Removed labels in use.',
                    'Some string matched the pattern `%s`, which has been '
                    'flagged as having been removed or renamed '
                    'in Thunderbird 31.' % pattern,
                    compat_type='error')


class RegexTest(object):
    """
    Compiles a list of regular expressions (or iterables of literal strings)
    into a singular regular expression, and emits warnings for each match.
    """

    def __init__(self, regexps):
        key = 'test_%d'

        self.tests = {key % i: data
                      for i, (regexp, data) in enumerate(regexps)}

        # Used in tests.
        self.regex_source = '|'.join(
            r'(?P<%s>%s)' % (key % i, self.process_key(regexp))
            for i, (regexp, data) in enumerate(regexps))

        self.regex = re.compile(self.regex_source)

    def process_key(self, key):
        """Processes a key into a regular expression. Currently turns an
        enumerable value into a regexp which matches a string which is
        exactly equal to any included value."""

        if isinstance(key, basestring):
            return key

        return r'^(?:%s)$' % '|'.join(map(re.escape, key))

    def test(self, string, traverser, properties=None, wrapper=None):
        for match in self.regex.finditer(string):
            for key, val in match.groupdict().iteritems():
                if val is not None and key in self.tests:
                    kw = {'err_id': ('testcases_regex', 'string', 'generic')}
                    kw.update(self.tests[key])
                    if properties:
                        kw.update(properties)

                    msg = traverser.warning(**kw)
                    if wrapper:
                        wrapper.value.messages.append(msg)


PROFILE_FILENAMES = (
    'SiteSecurityServiceState.txt',
    'addons.json',
    'addons.sqlite',
    'blocklist.xml',
    'cert8.db',
    'compatibility.ini',
    'compreg.dat',
    'content-prefs.sqlite',
    'cookies.sqlite',
    'directoryLinks.json',
    'extensions.ini',
    'extensions.json',
    'extensions.sqlite',
    'formhistory.sqlite',
    'healthreport.sqlite',
    'httpDataUsage.dat',
    'key3.db',
    'localstore.rdf',
    'logins.json',
    'permissions.sqlite',
    'places.sqlite',
    'places.sqlite-shm',
    'places.sqlite-wal',
    'pluginreg.dat',
    'prefs.js',
    'safebrowsing/*',
    'search-metadata.json',
    'search.json',
    'search.sqlite',
    'searchplugins/*',
    'secmod.db',
    'sessionCheckpoints.json',
    'sessionstore.js',
    'signons.sqlite',
    'startupCache/*',
    'urlclassifier.pset',
    'urlclassifier3.sqlite',
    'urlclassifierkey3.txt',
    'user.js',
    'webappsstore.sqlite',
    'xpti.dat',
    'xulstore.json')
# These tests have proved too generic, and will need fine tuning:
#   "healthreport/*",
#   "storage/*",
#   "webapps/*",


def munge_filename(name):
    # Changes filenames ending with `/*` into a regular expression which
    # will also match sub-paths across platforms. Escapes regex metacharacters
    # in other strings.
    if name.endswith('/*'):
        return r'%s(?:[/\\].*)?' % re.escape(name[:-2])
    return re.escape(name)

PROFILE_REGEX = r'(?:^|[/\\])(?:%s)$' % '|'.join(map(munge_filename,
                                                     PROFILE_FILENAMES))

STRING_REGEXPS = (
    # Unsafe files in the profile directory.
    (PROFILE_REGEX, {
        'err_id': ('testcases_regex', 'string', 'profile_filenames'),
        'warning': 'Reference to critical user profile data',
        'description': 'Critical files in the user profile should not be '
                       'directly accessed by add-ons. In many cases, an '
                       'equivalent API is available and should be used '
                       'instead.',
        'signing_help': 'Please avoid touching files in the user profile '
                        'which do not belong to your add-on. If the effects '
                        'that you are trying to achieve cannot be replicated '
                        'with a built-in API, we strongly encourage you to '
                        'remove this functionality.',
        'signing_severity': 'low'}),

    # The names of potentially dangerous category names for the
    # category manager.
    (DANGEROUS_CATEGORIES, DANGEROUS_CATEGORY_WARNING),

    # References to the obsolete extension manager API.
    (r'@mozilla\.org/extensions/manager;1|'
     r'em-action-requested',
     {'warning': 'Obsolete Extension Manager API',
      'description': 'The old Extension Manager API is not available in any '
                     'remotely modern version of Firefox and should not be '
                     'referenced in any code.'}),

    # References to the Marionette service.
    (r'@mozilla\.org/marionette;1', MARIONETTE_MESSAGE),
    (r'\{786a1369-dca5-4adc-8486-33d23c88010a\}', MARIONETTE_MESSAGE),
)

PREFERENCE_ERROR_ID = 'testcases_regex', 'string', 'preference'

PREF_REGEXPS = (
    tuple(
        (pattern,
         {'err_id': PREFERENCE_ERROR_ID,
          'warning': 'Potentially unsafe preference branch referenced',
          'description': 'Extensions should not alter preferences '
                         'matching /%s/.' % pattern})
        for pattern in BANNED_PREF_REGEXPS) +
    tuple(
        ('^%s' % re.escape(branch),
         merge_description(
             {'err_id': PREFERENCE_ERROR_ID,
              'warning': 'Potentially unsafe preference branch referenced'},
             reason or ('Extensions should not alter preferences in '
                        'the `%s` preference branch' % branch)))
        for branch, reason in BANNED_PREF_BRANCHES))

COMPAT_PREF_REGEXPS = [
    (r'\bbrowser.newtab.url\b', {
        'message': 'The browser.newtab.url preference has been removed.',
        'warning': 'The browser.newtab.url preference has been removed. You '
                   'can use the override function in NewTabURL.jsm instead. '
                   'See %s for more information.' %
                       'http://mxr.mozilla.org/mozilla-beta/source/browser/'
                       'modules/NewTabURL.jsm',
        'tier': 5,
        'for_appversions': FX41_DEFINITION,
        'compatibility_type': 'error',
    }),
]

# For tests in literal strings, add help text suggesting passing the
# preference directly to reference getter functions.
PREF_STRING_HELP = (
    'If you are reading, but not writing, this preference, please consider '
    'passing a string literal directly to `Preferences.get()` or '
    '`nsIPrefBranch.get*Pref`.')


def maybe_tuple(value):
    """Return `value` as a tuple. If it is already a tuple, return it
    unchanged. Otherwise return a 1-element tuple containing `value`."""

    if isinstance(value, tuple):
        return value
    return (value,)


def add_pref_help(desc):
    desc = desc.copy()
    for key in 'description', 'signing_help':
        if key in desc:
            desc[key] = maybe_tuple(desc[key]) + maybe_tuple(PREF_STRING_HELP)

    return desc

STRING_REGEXPS += tuple((pattern, add_pref_help(desc))
                        for pattern, desc in PREF_REGEXPS)

# The following patterns should only be flagged in strings we're certain are
# being passed to preference setter functions, so add them after appending
# the others to the literal string tests.
PREF_REGEXPS += (
    (r'.*password.*',
     {'err_id': PREFERENCE_ERROR_ID,
      'warning': 'Passwords should not be stored in preferences',
      'description': 'Storing passwords in preferences is insecure. '
                     'The Login Manager should be used instead.'}),
)

validate_string = RegexTest(STRING_REGEXPS).test
validate_pref = RegexTest(PREF_REGEXPS).test
validate_compat_pref = RegexTest(COMPAT_PREF_REGEXPS).test
