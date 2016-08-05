import json
import os
import sys
import unittest
from cStringIO import StringIO

from validator.validate import validate


FIREFOX_GUID = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
MOBILE_GUID = '{a23983c0-fd0e-11dc-95ff-0800200c9a66}'
THUNDERBIRD_GUID = '{3550f703-e582-4d05-9a08-453d09bdfdc6}'


def _validator(file_path, for_appversions=None, overrides=None):
    from validator.testcases import scripting
    import validator
    import validator.constants
    js = os.environ.get('SPIDERMONKEY_INSTALLATION', 'js')
    apps = os.path.join(os.path.dirname(validator.__file__),
                        'app_versions.json')
    if not os.path.exists(apps):
        raise EnvironmentError('Could not locate app_versions.json in git '
                               'repo for validator. Tried: %s' % apps)
    orig = sys.stderr
    sys.stderr = StringIO()
    try:
        result = validate(file_path, format='json',
                          # Test all tiers at once. This will make
                          # sure we see all error messages.
                          determined=True,
                          approved_applications=apps,
                          spidermonkey=js,
                          for_appversions=for_appversions,
                          timeout=60 * 3,  # seconds
                          overrides=overrides)
        sys.stdout.write(sys.stderr.getvalue())
        if 'Traceback' in sys.stderr.getvalue():
            # the validator catches and ignores certain errors in an attempt
            # to remain versatile.  There should not be any exceptions
            # while testing.
            raise RuntimeError(
                "An exception was raised during validation. Check stderr")
    finally:
        sys.stderr = orig
    return result


_cached_validation = {}


class ValidatorTest(unittest.TestCase):

    def setUp(self):
        self.validation = None
        self.messages = None
        self.ids = None

    def msg_set(self, d):
        return sorted(set([m['message'] for m in d['messages']]))

    def id_set(self, d):
        return set([tuple(m['id']) for m in d['messages']])

    def validate(self, xpi, **validate_kwargs):
        self.validation = self._run_validation(xpi, **validate_kwargs)
        self.messages = self.msg_set(self.validation)
        self.ids = self.id_set(self.validation)
        return self.validation

    def _cache_key(self, *vals):
        args = []
        for v in vals:
            self._flatten(args, v)
        return tuple(sorted(args))

    def _flatten(self, args, val):
        if isinstance(val, dict):
            for k, v in val.iteritems():
                self._flatten(args, k)
                self._flatten(args, v)
        elif isinstance(val, list):
            for v in val:
                self._flatten(args, v)
        else:
            args.append(val)

    def _run_validation(self, xpi, **validate_kwargs):
        path = os.path.join(os.path.dirname(__file__), 'addons', xpi)
        cache_key = self._cache_key(path, validate_kwargs)
        if cache_key in _cached_validation:
            return _cached_validation[cache_key]
        v = json.loads(_validator(path, **validate_kwargs))
        _cached_validation[cache_key] = v
        return v

    def assertPartialMsg(self, partial_msg):
        found = False
        for m in self.messages:
            if m.startswith(partial_msg):
                found = True
        assert found, ('Unexpected: %r' % self.messages)

    def expectMsg(self, msg):
        assert msg in self.messages, (
                    'Expected %r but only got %r' % (msg, self.messages))

    def shouldNotGetMsg(self, msg):
        assert msg not in self.messages, ('Did not expect %r' % (msg))

    def expectId(self, id):
        assert id in self.ids, (
                    'Expected %r but only got %r' % (id, self.ids))


class CompatValidatorTest(ValidatorTest):

    def validate_for_appver(self, xpi, app_guid, app_ver):
        overrides = {'targetapp_maxVersion': {app_guid: app_ver}}
        return self.validate(xpi, overrides=overrides,
                             for_appversions={app_guid: [app_ver]})


class JavaScriptTests(ValidatorTest):

    def test_createelement__used(self):
        self.validate('glee-20101227219.xpi')
        self.assertPartialMsg('createElement() used to create script tag')

    def test_dangerous_global(self):
        self.validate('feedly-addon-201101111013.xpi')
        self.expectMsg(u"`setTimeout` called in potentially "
                       u"dangerous manner")

    def test_global_called(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u"`setTimeout` called in potentially "
                       u"dangerous manner")

    def test_potentially_malicious(self):
        self.validate('add-on201101101027.xpi')
        self.expectMsg(u'DOM Mutation Events Prohibited')

    def test_variable_element(self):
        self.validate('glee-20101227219.xpi')
        self.expectMsg(u'Variable element type being created')


class GeneralTests(ValidatorTest):

    def test_contains_jar_files(self):
        self.validate('test-theme-3004.jar')
        self.expectMsg(u'Add-on contains JAR files, no <em:unpack>')

    def test_potentially_illegal_name(self):
        self.validate('add-on20110110322.xpi')
        self.expectMsg(u'Add-on has potentially illegal name.')

    def test_banned_element(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Banned element in install.rdf')

    def test_blacklisted_file(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Flagged file extensions found.')

    def test_blacklisted_file_2(self):
        self.validate('peerscape-3.1.5-fx.xpi')
        self.expectMsg(u'Flagged file type found')

    def test_em_type_not(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'No <em:type> element found in install.rdf')

    def test_obsolete_element(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Banned element in install.rdf')

    def test_unknown_file(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Unrecognized element in install.rdf')

    def test_unrecognized_element(self):
        self.validate('littlemonkey-1.8.56-sm.xpi')
        self.expectMsg(u'Add-on missing manifest.')

    def test_invalid_id(self):
        self.validate('add-ongoogle-201101121132.xpi')
        self.expectMsg(u'The value of <em:id> is invalid')

    def test_xpi_cannot(self):
        self.validate('lavafox_test-theme-20101130538.xpi')
        self.expectMsg(u'Corrupt ZIP file')

    def test_invalid_version(self):
        self.validate('invalid maximum version number.xpi')
        self.expectMsg(u'Invalid maximum version number')

    def test_non_ascii_html_markup(self):
        # should be no Unicode errors
        self.validate('non-ascii-html.xpi')

    def test_webextension_seen_as_extension(self):
        validation = self.validate('beastify.xpi')
        assert validation['detected_type'] == 'extension'
        assert validation['errors'] == 0

    def test_install_rdf_and_manifest_json(self):
        validation = self.validate('installrdf-and-manifestjson.xpi')
        assert validation['detected_type'] == 'extension'
        assert validation['errors'] == 0


class LocalizationTests(ValidatorTest):

    def test_translation(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Unchanged translation entities')

    def test_encodings(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Unexpected encodings in locale files')

    def test_missing_translation(self):
        self.validate('download_statusbar-0.9.7.2-fx (1).xpi')
        self.expectMsg(u'Missing translation entity')


class SecurityTests(CompatValidatorTest):

    def test_missing_comments(self):
        self.validate('add-on-20110113408.xpi')
        self.expectMsg(u'Global variable overwrite')

    def test_typeless_iframes_browsers(self):
        self.validate('add-on201101081038.xpi')
        self.expectMsg(u'Typeless iframes/browsers must be local.')

    def test_binary_files(self):
        self.validate_for_appver('cooliris-1.12.2.44172-fx-mac.xpi.xpi',
                                 FIREFOX_GUID, '5.0a2')
        self.expectMsg(u"Flagged file extensions found.")
        self.expectMsg(u"Flagged file type found")
        self.expectId(('testcases_packagelayout',
                       'test_compatibility_binary',
                       'disallowed_file_type'))

    def test_thunderbird_binary_files(self):
        self.validate_for_appver('enigmail-1.2-sm-windows.xpi',
                                 THUNDERBIRD_GUID, '6.0a1')
        self.expectMsg(u"Flagged file extensions found.")
        self.expectId(('testcases_packagelayout',
                       'test_compatibility_binary',
                       'disallowed_file_type'))


class NoErrorsExpected(ValidatorTest):

    def test_an_attempt(self):
        d = self.validate('tmp.xpi')
        assert d['errors'] == 0

    def test_don_t_freak(self):
        d = self.validate('test (1).xpi')
        assert d['errors'] == 0

    def test_don_t_freak_2(self):
        d = self.validate('littlemonkey-1.8.56-sm.xpi')
        msg = self.msg_set(d)
        ok = True
        for m in msg:
            if 'install.js' in msg:
                ok = False
        assert ok, ('Unexpected: %r' % msg)

    def test_unknown_file(self):
        d = self.validate('add-on20101228444 (1).jar')
        assert d['errors'] == 0

    def test_chromemanifest_traceback(self):
        d = self.validate('chromemanifest-traceback.jar')
        assert d['errors'] == 0


class SearchTools(ValidatorTest):

    def test_opensearch_providers(self):
        self.validate('sms_search-20110115 .xml')
        self.expectMsg(u'OpenSearch: <Url> elements may not be rel=self')

    def test_opensearch_shortname(self):
        self.validate('lexisone_citation_search-20100116 .xml')
        self.expectMsg(u'OpenSearch: <ShortName> element too long')

    def test_too_many(self):
        self.validate('addon-12201-latest.xml')
        self.expectMsg(u'OpenSearch: Too many <ShortName> elements')


class JetpackDetection(ValidatorTest):

    def test_jetpack_one_signing(self):
        results = self.validate('jetpack-one.xpi')
        assert results['signing_summary']['high'] == 0

    def test_jetpack_one_jetpack(self):
        results = self.validate('jetpack-one.xpi')
        assert results['metadata']['jetpack_identified_files']

    def test_jetpack_two_signing(self):
        results = self.validate('jetpack-two.xpi')
        assert results['signing_summary']['high'] == 0

    def test_jetpack_two_jetpack(self):
        results = self.validate('jetpack-two.xpi')
        assert results['metadata']['jetpack_identified_files']

    def test_jetpack_fail_for_cfx_usage(self):
        self.validate('cfx.xpi')
        self.expectMsg(u'Add-ons built with "cfx" are no longer accepted.')
