import json

from mock import patch

import validator
from validator import constants
from validator.validate import validate

from .helper import TestCase


class TestValidate(TestCase):

    def runValidation(self, path, **kwargs):
        self.output = validate(path=path, **kwargs)

    def test_metadata(self):
        """Test that the generated JSON has the appropriate metadata
        values."""
        self.runValidation('tests/resources/packagelayout/theme.jar')
        j = json.loads(self.output)
        assert j['metadata']['name'] == 'name_value'
        assert j['metadata']['validator_version'] == validator.__version__

    def test_metadata_bundle(self):
        """
        Test that the error bundle returned by validate() has the appropriate
        values within it.
        """
        self.runValidation('tests/resources/packagelayout/theme.jar',
                           format=None)
        assert self.output.metadata['name'] == 'name_value'

    def test_spidermonkey(self):
        """
        Test that the appropriate path for Spidermonkey is set through the
        `validate()` function.
        """
        self.runValidation('tests/resources/packagelayout/theme.jar',
                           format=None)
        assert self.output.determined
        assert self.output.get_resource('listed')

    def test_undetermined(self):
        """
        Test that when the validation is run with `determined=False`, that
        value is pushed through the full validation process.
        """
        self.runValidation('tests/resources/packagelayout/theme.jar',
                           format=None, determined=False)
        assert not self.output.determined
        assert self.output.get_resource('listed')
        assert self.output.metadata['listed'] is True

    def test_unlisted(self):
        """
        Test that when the validation is run with `listed=False`, that value
        is pushed through the full validation process.
        """
        self.runValidation('tests/resources/packagelayout/theme.jar',
                           format=None, listed=False)
        assert self.output.determined
        assert not self.output.get_resource('listed')
        assert self.output.metadata['listed'] is False

    def test_overrides(self):
        """
        Test that when the validation is run with `overrides={"foo": "foo"}`,
        that value is pushed through the full validation process.
        """
        self.runValidation('tests/resources/packagelayout/theme.jar',
                           format=None, overrides={'foo': 'foo'})
        assert self.output.determined
        assert self.output.get_resource('listed')
        assert self.output.overrides == {'foo': 'foo'}


@patch.dict('validator.constants.APPROVED_APPLICATIONS')
def test_app_versions():
    'Tests that the validate function properly loads app_versions.json'
    validate(path='tests/resources/junk.xpi',
             approved_applications='tests/resources/test_app_versions.json')
    assert constants.APPROVED_APPLICATIONS['1']['name'] == 'Foo App'


@patch.dict('validator.constants.APPROVED_APPLICATIONS')
def test_app_versions_dict():
    """
    Test that `approved_applications` can be provided as a pre-parsed dict
    of versions.
    """
    with open('tests/resources/test_app_versions.json') as f:
        apps = json.load(f)
    validate(path='tests/resources/junk.xpi', approved_applications=apps)
    assert constants.APPROVED_APPLICATIONS['1']['name'] == 'Foo App'


def test_is_compat():
    """Test that we know when we're running a compatibility test."""
    out = validate(path='tests/resources/junk.xpi', format=None,
                   compat_test=False)
    assert not out.get_resource('is_compat_test')

    out = validate(path='tests/resources/junk.xpi', format=None,
                   compat_test=True)
    assert out.get_resource('is_compat_test')


def test_validate_webextension():
    """Integration test for a basic webextension, without mocks.

    We're not supposed to use amo-validator for webextensions anymore now that
    we have addons-linter, but let's make sure that we don't completely
    blow up anyway."""
    result = validate(path='tests/resources/validate/webextension.xpi')
    data = json.loads(result)

    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert data['messages'] == []
    assert data['message_tree'] == {}
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_old_xpi():
    for is_compat_test in [True, False]:
        _test_validate_old_xpi(compat_test=is_compat_test)


def _test_validate_old_xpi(compat_test):
    """Integration test for a basic old-style extension xpi, without mocks."""
    result = validate(path='tests/resources/validate/extension.xpi',
                      compat_test=compat_test)
    data = json.loads(result)

    assert data['success'] is False
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 1
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert len(data['messages']) == 1
    assert data['messages'][0]['id'] == [
        u'submain', u'test_inner_package', u'not_multiprocess_compatible']
    assert data['message_tree']
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'name_value'
    assert data['metadata']['version'] == u'1.2.3.4'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'bastatestapp1@basta.mozilla.com'
    assert data['metadata']['strict_compatibility'] is True
    assert data['metadata']['applications']
    assert data['metadata']['applications']['firefox'] == {
        'min': '3.6', 'max': '3.6.*'
    }
    assert data['metadata']['applications']['mozilla'] == {
        'min': '1.0', 'max': '1.8+'
    }
    assert data['metadata']['is_extension'] is True


def test_validate_old_xpi_with_jar_in_it():
    """Integration test for a basic old-style extension xpi that contains a
    .jar file, without mocks."""
    result = validate(path='tests/resources/validate/extension_with_jar.xpi')
    data = json.loads(result)

    assert data['success'] is False
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 1
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert len(data['messages']) == 1
    assert data['messages'][0]['id'] == [
        u'submain', u'test_inner_package', u'not_multiprocess_compatible']
    assert data['message_tree']
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'xpi name'
    assert data['metadata']['version'] == u'0.2'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'guid@xpi'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_old_xpi_thunderbird_only():
    """Integration test for a thunderbird-only old-style extension xpi
    without mocks."""
    result = validate(
        path='tests/resources/validate/thunderbird_extension.xpi')
    data = json.loads(result)

    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert data['messages'] == []
    assert data['message_tree'] == {}
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'name_value'
    assert data['metadata']['version'] == u'1.2.3.4'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'bastatestapp1@basta.mozilla.com'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_old_xpi_multiprocess_compatible():
    for is_compat_test in [True, False]:
        _test_validate_old_xpi_multiprocess_compatible(
            compat_test=is_compat_test)


def _test_validate_old_xpi_multiprocess_compatible(compat_test):
    """Integration test for a multiprocess compatible old-style extension xpi,
    without mocks."""
    result = validate(
        path='tests/resources/validate/extension_multiprocess.xpi',
        compat_test=compat_test)
    data = json.loads(result)

    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert data['messages'] == []
    assert data['message_tree'] == {}
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'name_value'
    assert data['metadata']['version'] == u'1.2.3.4'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'bastatestapp1@basta.mozilla.com'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_jpm():
    for is_compat_test in [True, False]:
        _test_validate_jpm(compat_test=is_compat_test)


def _test_validate_jpm(compat_test):
    """Integration test for a basic jpm-style extension xpi, without mocks."""
    result = validate(path='tests/resources/validate/jpm.xpi',
                      compat_test=compat_test)
    data = json.loads(result)

    assert data['success'] is False
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 1
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert len(data['messages']) == 1
    assert data['messages'][0]['id'] == [
        u'submain', u'test_inner_package', u'not_multiprocess_compatible']
    assert data['message_tree']
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'My Jetpack Addon'
    assert data['metadata']['version'] == u'0.0.3'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'@test-addon'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_jpm_multiprocess_compatible():
    for is_compat_test in [True, False]:
        _test_validate_jpm_multiprocess_compatible(compat_test=is_compat_test)


def _test_validate_jpm_multiprocess_compatible(compat_test):
    """Integration test for a multiprocess compatible jpm-style extension xpi,
    without mocks."""
    result = validate(path='tests/resources/validate/jpm_multiprocess.xpi',
                      compat_test=compat_test)
    data = json.loads(result)

    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'
    assert data['messages'] == []
    assert data['message_tree'] == {}
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'My Jetpack Addon'
    assert data['metadata']['version'] == u'0.0.3'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'@test-addon'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True


def test_validate_dictionnary_no_multiprocess_compatible_warning():
    """Integration test for a dictionnary xpi, without mocks."""
    result = validate(path='tests/resources/validate/dictionary.xpi')
    data = json.loads(result)
    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 0
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'dictionary'
    assert data['messages'] == []
    assert data['message_tree'] == {}
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'My Fake Dictionary'
    assert data['metadata']['version'] == u'1.0.0'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'my@dict'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is False


def test_validate_theme():
    result = validate(path='tests/resources/validate/theme.xpi')
    data = json.loads(result)
    assert data['metadata']['is_extension'] is False


def test_validate_search():
    result = validate(path='tests/resources/validate/search.xml')
    data = json.loads(result)
    assert data['metadata']['is_extension'] is False


def test_validate_language_pack():
    result = validate(path='tests/resources/validate/langpack.xpi')
    data = json.loads(result)
    assert data['metadata']['is_extension'] is False


def test_validate_embedded_webextension_xpi():
    """Integration test for the expected notice message on 'embedded
    webextension' add-ons."""

    err_bundle = validate(
        path='tests/resources/validate/hybrid_extension.xpi', format=None)
    assert err_bundle.get_resource('has_embedded_webextension') is True

    result = validate(path='tests/resources/validate/hybrid_extension.xpi')
    data = json.loads(result)

    assert data['success'] is True
    assert data['errors'] == 0
    assert data['notices'] == 1
    assert data['warnings'] == 0
    assert data['compatibility_summary']
    assert data['compatibility_summary']['errors'] == 0
    assert data['compatibility_summary']['notices'] == 0
    assert data['compatibility_summary']['warnings'] == 0
    assert data['detected_type'] == 'extension'

    assert len(data['messages']) == 1
    assert data['messages'][0]['file'] == u'install.rdf'
    assert data['messages'][0]['message'] == (
        u'This add-on contains an embedded webextension')

    expected_embedded_webext_desc = (
        'The embedded webextension is in the folder "webextension"')
    expected_embedded_webext_doc_url = (
        'https://developer.mozilla.org/en-US/Add-ons/WebExtensions/'
        'Embedded_WebExtensions')

    messages = data['messages']
    assert expected_embedded_webext_desc in messages[0]['description']
    assert expected_embedded_webext_doc_url in messages[0]['description']

    assert data['message_tree']
    assert data['signing_summary']['high'] == 0
    assert data['signing_summary']['medium'] == 0
    assert data['signing_summary']['low'] == 0
    assert data['signing_summary']['trivial'] == 0
    assert data['metadata']
    assert data['metadata']['name'] == u'name_value'
    assert data['metadata']['version'] == u'1.2.3.4'
    assert data['metadata']['listed'] is True
    assert data['metadata']['id'] == u'an-hybrid-addon@mozilla.com'
    assert data['metadata'].get('strict_compatibility') is None
    assert data['metadata']['is_extension'] is True
