"""Contains regular expression tests for compatibility runs."""
from validator.compat import (FX38_DEFINITION, FX39_DEFINITION,
                              FX40_DEFINITION,
                              TB29_DEFINITION, TB30_DEFINITION,
                              TB31_DEFINITION)
from validator.constants import BUGZILLA_BUG, MDN_DOC

from .generic import FileRegexTest


def get_compat_tests(err):
    """Return an appropriate compatibility tester for the given
    ErrorBundle."""

    if 'compat_regex_tests' not in err.resources:
        err.resources['compat_regex_tests'] = CompatRegexTest(
            err, COMPAT_REGEXPS)

    return err.resources['compat_regex_tests']


class CompatRegexTest(FileRegexTest):
    """Matches compatibility test regular expressions against the entire text
    files. Limits the tests it performs based on the application versions
    supported by a given ErrorBundle."""

    TEST_ID = ('testcases_regex', 'compat')

    def __init__(self, err, tests):
        patterns = self.get_patterns(err, tests)
        super(CompatRegexTest, self).__init__(patterns)

    def get_patterns(self, err, tests):
        """Return pattern-test pairs for each test set that matches the
        compatiblity range of our error bundle."""

        for compat_version, patterns in tests:
            if err.supports_version(compat_version):
                for key, pattern in patterns:
                    pattern.setdefault('for_appversions', compat_version)
                    pattern.setdefault('compatibility_type', 'error')
                    pattern.setdefault('tier', 5)
                    yield key, pattern


class CheapCompatBugPatternTests(object):
    def __init__(self, app_version_name, patterns):
        self.app_version_name = app_version_name
        self.patterns = patterns

    def __iter__(self):
        for pattern, bug in self.patterns.iteritems():
            yield (pattern,
                   {'warning': 'Flagged pattern matched: {0}'.format(pattern),
                    'description': (
                        'Code matching this pattern has been flagged as '
                        'compatibility issue for {app_version}. See {bug} for '
                        'more information.'.format(
                            app_version=self.app_version_name,
                            bug=BUGZILLA_BUG % bug))})


# FIXME: Most of these should not be regular expression tests.
COMPAT_REGEXPS = [
    (FX38_DEFINITION, (
        (r'\bmozIndexedDB\b',
         {'warning': 'mozIndexedDB has been removed.',
          'description': 'mozIndexedDB has been removed. You should use '
                         'indexedDB instead. '
                         'See %s for more information.'
                         % BUGZILLA_BUG % 975699}),

        (r'\b(?:nsICompositionStringSynthesizer|sendCompositionEvent|'
         r'createCompositionStringSynthesizer)\b',

         {'warning': 'nsICompositionStringSynthesizer, '
                     'sendCompositionEvent, and '
                     'createCompositionStringSynthesizer were removed.',

          'description': (
              'The nsICompositionStringSynthesizer interface and the '
              'sendCompositionEvent and createCompositionStringSynthesizer '
              'functions have been removed. See %s for more information.'
              % MDN_DOC
              % ('Mozilla/Tech/XPCOM/Reference/Interface/'
                 'nsITextInputProcessor')),
          }),

        (r'\b(?:newChannel2|asyncFetch2)\b',
         {'warning': 'asyncFetch2 and newChannel2 are now deprecated.',
          'description': 'asyncFetch2 and newChannel2 are now deprecated. '
                         'Use asyncFetch or newChannel instead. See %s for '
                         'more information.' % BUGZILLA_BUG % 1125618,
          'compatibility_type': 'warning'}),

        (r'\b(onProxyAvailable|asyncResolve)\b',
         {'warning': 'The onProxyAvailable and asyncResolve functions have '
                     'changed.',
          'description': 'They now take an nsIChannel instead of an nsIURI '
                         'as an argument. '
                         'See %s for more information.'
                         % BUGZILLA_BUG % 436344}),
    )),

    (FX39_DEFINITION, (
        (r'\b__noSuchMethod__\b',
         {'warning': 'The __noSuchMethod__ property has been deprecated.',
          'description': (
              'The __noSuchMethod__ property has been deprecated. See %s for '
              'more information.'
              % MDN_DOC % ('Web/JavaScript/Reference/Global_Objects/Object/'
                           'noSuchMethod')),
          'compatibility_type': 'warning'}),

        (r'\bsendAsBinary\b',
         {'warning': 'The function sendAsBinary() in XMLHttpRequest has been '
                     'removed.',
          'description': (
              'The function sendAsBinary() in XMLHttpRequest has been '
              'removed. You can use send() with a Blob instead. '
              'See %s for more information.' % BUGZILLA_BUG % 853162)}),

        (r'\blightweightThemes\.(usedThemes|isThemeSelected)\b',
         {'warning': 'The preferences used to store theme selection have '
                     'changed.',
          'description': 'The preferences used to store theme selection have '
                         'changed. See %s#c39 for more information.'
                         % BUGZILLA_BUG % 1094821}),
    )),

    (FX40_DEFINITION, (
        (r'\b([gs]etKeywordForBookmark|getURIForKeyword)\b',
         {'warning': 'The old keywords API is deprecated.',
          'description': (
            'The old keywords API is deprecated. You should use '
            'PlacesUtils.keywords instead. See %s for more information.'
            % MDN_DOC % 'Mozilla/Tech/Places/Using_the_Places_keywords_API'),
          'compatibility_type': 'warning'}),

        (r'\b(fuelIApplication|extIApplication)\b',
         {'warning': 'The FUEL library is now deprecated.',
          'description': (
            'The FUEL library is now deprecated. You should use the add-ons '
            'SDK or Services.jsm. See %s for more information.'
            % MDN_DOC % 'Mozilla/Tech/Toolkit_API/FUEL'),
          'compatibility_type': 'warning'}),

        (r'\bresource://gre/modules/Dict.jsm\b',
         {'warning': 'The Dict.jsm module has been removed.',
          'description': (
            'The Dict.jsm module has been removed. You can use the native Map '
            'object instead. See %s for more information.'
            % MDN_DOC % 'Web/JavaScript/Reference/Global_Objects/Map'),
          'compatibility_type': 'error'}),

        (r'\bsessionstore-state-write\b',
         {'warning': "The \"sessionstore-state-write\" notification has been "
                     'removed.',
          'description': (
            "The \"sessionstore-state-write\" notification has been removed. "
            'See %s for more information.' % BUGZILLA_BUG % 1157235),
          'compatibility_type': 'error'}),

        (r'\bnsISSLErrorListener\b',
         {'warning': 'The nsISSLErrorListener interface has been removed.',
          'description': (
            'The nsISSLErrorListener interface has been removed. See %s for '
            'more information.' % BUGZILLA_BUG % 844351),
          'compatibility_type': 'error'}),

        (r"""require\(['"]sdk/widget['"]\)""",
         {'warning': 'The widget module has been removed.',
          'description': (
            'The widget module has been removed. You can use ActionButton or '
            'ToggleButton instead. See %s for more information.'
            % 'https://developer.mozilla.org/en-US/Add-ons/SDK/'
              'High-Level_APIs/widget'),
          'compatibility_type': 'error'}),
    )),

    # Thunderbird compatibility tests.
    (TB29_DEFINITION, CheapCompatBugPatternTests('Thunderbird 29', {
        r'update\.checkingAddonCompat': 707489,
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
        r'dateformat': 544315})),

    (TB30_DEFINITION, CheapCompatBugPatternTests('Thunderbird 30', {
        r'log\.lastWeek': 863226,
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
        r'bounceSystemDockIcon\.accesskey': 601263})),

    (TB31_DEFINITION, CheapCompatBugPatternTests('Thunderbird 31', {
        r'youSendItMgmt\.viewSettings': 894306,
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
        r'mailnews\.reply_header_ondate': 995797})),
]
