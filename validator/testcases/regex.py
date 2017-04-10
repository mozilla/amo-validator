import re
from functools import wraps

from validator.compat import (
    FX45_DEFINITION, FX46_DEFINITION, FX47_DEFINITION, FX48_DEFINITION,
    FX50_DEFINITION, FX51_DEFINITION, FX52_DEFINITION, FX53_DEFINITION,
    FX54_DEFINITION)
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
                 compat_type=None, app_versions=None, flags=0, editors_only=False):
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
                      'tier': self.err.tier if app_versions is None else 5,
                      'editors_only': editors_only}

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


@register_generator
class XPIProviderRegexTests(RegexTestGenerator):
    """
    These regex tests ensure that developers are not using the XPIProvider
    or AddonManagerInternal symbols.

    Added from bug 1200929.
    """

    def tests(self):
        msg = 'Access to AddonManagerInternal and XPIProvider is not allowed.'

        yield self.get_test(
            r'\b(XPIProvider|AddonManagerInternal)\b',
            msg, {'description': msg, 'signing_severity': 'high'})


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
class unblockerytRegexTests(RegexTestGenerator):
    """
    Checks for the use of `unblocker.yt` which is used by a dangerous add-on.
    """

    def tests(self):
        yield self.get_test(
                r'unblocker\.yt',
                'Potentially malicious domain usage.',
                'This add-on uses a potentially malicious domain. Please '
                'escalate for admin review.',
                editors_only=True)


@register_generator
class Gecko45RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 45 updates."""

    VERSION = FX45_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\bnsIURIChecker\b',
            'The nsIURIChecker interface has been removed',
            'The nsIURIChecker interface has been removed. '
            'See %s for more information.' % BUGZILLA_BUG % 1222829,
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\b(gProxyFavIcon|\"page-proxy-favicon\")\b',
            (
                'The site identity interface has changed, '
                'which means gProxyFavIcon and "page-proxy-favicon" '
                'are no longer valid.'
            ),
            (
                'The site identity interface has changed, '
                'which means gProxyFavIcon and "page-proxy-favicon" '
                'are no longer valid. See %s for more information'
                % BUGZILLA_BUG % 1206244
            ),
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\bremoveAllPages\b',
            'The removeAllPages function is now deprecated.',
            'The removeAllPages function is now deprecated. '
            'You should use PlacesUtils.history.clear(); instead. '
            'See %s for more information.' % BUGZILLA_BUG % 1124185,
            log_function=self.err.warning,
            compat_type='warning')


@register_generator
class Gecko46RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 46 updates."""

    VERSION = FX46_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\b(mTabListeners|mTabFilters)\b',
            (
                'mTabListeners and mTabFilters are now Map objects and have '
                'been renamed to _tabListeners and _tabFilters, respectively.'
            ),
            (
                'mTabListeners and mTabFilters are now Map objects and have '
                'been renamed to _tabListeners and _tabFilters, respectively. '
                'See %s for more information' % BUGZILLA_BUG % 1238685
            ),
            log_function=self.err.warning,
            compat_type='error')


@register_generator
class Gecko47RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 47 updates."""

    VERSION = FX47_DEFINITION

    def tests(self):
        yield self.get_test(
            r'\bgDevTools\.jsm\b',
            'The gDevTools.jsm module should no longer be used.',
            (
                'The gDevTools.jsm module should no longer be used. '
                'The object should now be loaded using '
                'require("devtools/client/framework/devtools"). See '
                '%s for more information.' % BUGZILLA_BUG % 1188405
            ),
            log_function=self.err.warning,
            compat_type='warning')

        yield self.get_test(
            r'\b(CustomizationTabPreloader|about:customizing)\b',
            'The customization panel is no longer loaded via about:customizing.',
            (
                'The customization panel is no longer loaded via about:customizing. '
                'See %s for more information.' % BUGZILLA_BUG % 1014185
            ),
            log_function=self.err.warning,
            compat_type='error')

    def js_tests(self):
        yield self.get_test(
            r'\b(fuelIApplication|extIApplication)\b',
            'The FUEL library is no longer supported.',
            'The FUEL library is no longer supported. Please use the Add-ons '
            'SDK instead. See %s for more information.' % MDN_DOC % 'Add-ons/SDK',
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test(
            r'\bnsIX509CertDB\b',
            'Most methods in nsIX509CertDB had their unused arguments removed.',
            (
                'Most methods in nsIX509CertDB had their unused arguments '
                'removed. See %s for more information.' % BUGZILLA_BUG % 1241646
            ),
            log_function=self.err.warning,
            compat_type='error')


@register_generator
class Gecko48RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 48 updates."""

    VERSION = FX48_DEFINITION

    def tests(self):
        instances = (
            'chrome://global/skin/icons/loading_16\.png|'
            'chrome://browser/skin/tabbrowser/loading\.png')

        msg = (
            'The throbber icon your add-on points to has been '
            'moved to "chrome://global/skin/icons/loading.png".')

        yield self.get_test(
            r'\b(%s)\b' % instances,
            msg,
            msg + ' See %s for more information.' % BUGZILLA_BUG % 750054,
            log_function=self.err.warning,
            compat_type='warning'
        )


@register_generator
class Gecko50RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 50 updates."""

    VERSION = FX50_DEFINITION

    def tests(self):
        instances = ('draggesture', 'dragdrop', 'ondraggesture', 'ondragdrop')

        msg = (
            'The draggesture and dragdrop events are no longer supported. '
            'You should use the standard equivalents instead: '
            'dragstart and drop.')

        description = (
            msg + ' See %s for more information.'
            % MDN_DOC % 'Web/API/HTML_Drag_and_Drop_API')

        yield self.get_test(
            r'[\'"]?(%s)([\'"]|=)' % ('|'.join(instances)),
            msg,
            description,
            log_function=self.err.warning,
            compat_type='error'
        )


@register_generator
class Gecko51RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 51 updates."""

    VERSION = FX51_DEFINITION

    def tests(self):
        yield self.get_test_bug(
            528005,
            r'\bBrowserOpenNewTabOrWindow\b',
            'The function BrowserOpenNewTabOrWindow has been removed.',
            'You can use BrowserOpenTab instead, but its behavior is not identical. ',
            log_function=self.err.warning,
            compat_type='error',
        )

        yield self.get_test_bug(
            812701,
            r'\b(%s)\b' % ('|'.join(('mozVisibilityState', 'mozHidden'))),
            'The mozVisibilityState and mozHidden properties are no longer prefixed.',
            'You should use visibilityState and hidden instead.',
            log_function=self.err.warning,
            compat_type='error'
        )

        yield self.get_test_bug(
            1167575,
            r'\bonButtonClick\b',
            'The function onButtonClick is now asynchronous.',
            message='',
            log_function=self.err.warning,
            compat_type='error'
        )


@register_generator
class Gecko52RegexTests(CompatRegexTestHelper):
    """Regex tests for Firefox 52 updates."""

    VERSION = FX52_DEFINITION

    def tests(self):
        yield self.get_test_bug(
            931389,
            r'\b(%s)\b' % ('|'.join(('mozDash', 'mozDashOffset'))),
            'The mozDash and mozDashOffset properties are no longer supported.',
            'You can use setLineDash() instead.',
            log_function=self.err.warning,
            compat_type='error'
        )


@register_generator
class Gecko53RegexTests(CompatRegexTestHelper):
    VERSION = FX53_DEFINITION

    def tests(self):
        yield self.get_test_bug(
            1321556,
            r'\burlbarBindings\.xml#splitmenu\b',
            'The splitmenu element has been removed.',
            'The splitmenu element has been removed.',
            log_function=self.err.warning,
            compat_type='error')

        yield self.get_test_bug(
            1331296,
            r'-moz-calc\b',
            'The -moz-calc function has been removed.',
            'You can use the equivalent calc instead',
            log_function=self.err.warning,
            compat_type='warning')

        # This needs a regex test since most add-ons I could find
        # actually overwrite this method in various ways which we cannot
        # match properly via traversing the AST.
        msg = (
            'The _openURIInNewTab function was changed and now requires '
            'an nsIURI for the referrer.')

        yield self.get_test_bug(
            1147911,
            r'\b_openURIInNewTab\b',
            msg,
            msg,
            log_function=self.err.warning,
            compat_type='error')


@register_generator
class Gecko54RegexTests(CompatRegexTestHelper):
    VERSION = FX54_DEFINITION

    def tests(self):
        yield self.get_test_bug(
            1333482,
            r'-moz-appearance\b',
            '-moz-appearance can only be used in chrome stylesheets.',
            'All other uses will be ignored.',
            log_function=self.err.warning,
            compat_type='warning')


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
