"""Contains regular expression tests which run against the parsed contents
of JavaScript string literals."""
import re

from validator.errorbundler import maybe_tuple, merge_description
from ..chromemanifest import DANGEROUS_CATEGORIES, DANGEROUS_CATEGORY_WARNING
from ..javascript.predefinedentities import (BANNED_PREF_BRANCHES,
                                             BANNED_PREF_REGEXPS,
                                             MARIONETTE_MESSAGE)

from .base import RegexTestBase


class JSRegexTest(RegexTestBase):
    """Matches regular expressions in JavaScript string literals."""

    TEST_ID = ('testcases_regex', 'string')

    def report_match(self, test, traverser, wrapper=None, **kw):
        msg = super(JSRegexTest, self).report_match(test, err=traverser, **kw)

        # Save the message to the JSValue of the string we're testing, so
        # later tests against the same string have access to it.
        if wrapper:
            wrapper.value.messages.append(msg)


def munge_filename(name):
    """Mangle a filename into a regular expression which will match that
    exact filename.

    Filenames ending in `/*` will also match sub-paths, in a platform-agnostic
    manner."""
    if name.endswith('/*'):
        return r'%s(?:[/\\].*)?' % re.escape(name[:-2])
    return re.escape(name)


# Filenames in the profile directory which should not be touched by add-ons.
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


STRING_REGEXPS = [
    # Unsafe files in the profile directory.
    (r'(?:^|[/\\])(?:%s)$' % '|'.join(map(munge_filename, PROFILE_FILENAMES)),
     {'err_id': ('testcases_regex', 'string', 'profile_filenames'),
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
    (('@mozilla.org/extensions/manager;1', 'em-action-requested'),
     {'warning': 'Obsolete Extension Manager API',
      'description': 'The old Extension Manager API is not available in any '
                     'remotely modern version of Firefox and should not be '
                     'referenced in any code.'}),

    # References to the Marionette service.
    (('@mozilla.org/marionette;1',
      '{786a1369-dca5-4adc-8486-33d23c88010a}'), MARIONETTE_MESSAGE),
]

PREFERENCE_ERROR_ID = 'testcases_regex', 'string', 'preference'

PREF_REGEXPS = []

# Match exact preference names from BANNED_PREF_REGEXPS.
PREF_REGEXPS.extend(
    (pattern,
     {'err_id': PREFERENCE_ERROR_ID,
      'warning': 'Potentially unsafe preference branch referenced',
      'description': 'Extensions should not alter preferences '
                     'matching /%s/.' % pattern})
    for pattern in BANNED_PREF_REGEXPS)

# Match any preference under each branch in BANNED_PREF_BRANCHES.
PREF_REGEXPS.extend(
    ('^%s' % re.escape(branch),
     merge_description(
         {'err_id': PREFERENCE_ERROR_ID,
          'warning': 'Potentially unsafe preference branch referenced'},
         reason or ('Extensions should not alter preferences in '
                    'the `%s` preference branch' % branch)))
    for branch, reason in BANNED_PREF_BRANCHES)


# For tests in literal strings, add help text suggesting passing the
# preference directly to preference getter functions.
def add_pref_help(desc):
    desc = desc.copy()
    for key in 'description', 'signing_help':
        if key in desc:
            desc[key] = maybe_tuple(desc[key]) + maybe_tuple(PREF_STRING_HELP)

    return desc

PREF_STRING_HELP = (
    'If you are reading, but not writing, this preference, please consider '
    'passing a string literal directly to `Preferences.get()` or '
    '`nsIPrefBranch.get*Pref`.')

STRING_REGEXPS.extend((pattern, add_pref_help(desc))
                      for pattern, desc in PREF_REGEXPS)


# The following patterns should only be flagged in strings we're certain are
# being passed to preference setter functions, so add them after appending
# the others to the literal string tests.
PREF_REGEXPS.append(
    (r'.*password.*',
     {'err_id': PREFERENCE_ERROR_ID,
      'warning': 'Passwords should not be stored in preferences',
      'description': 'Storing passwords in preferences is insecure. '
                     'The Login Manager should be used instead.'}),
)


validate_string = JSRegexTest(STRING_REGEXPS).test
validate_pref = JSRegexTest(PREF_REGEXPS).test
