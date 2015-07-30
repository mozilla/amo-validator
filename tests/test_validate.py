import json

from mock import patch
from nose.tools import eq_

import validator
from validator import constants
from validator.validate import validate

from .helper import TestCase


class TestValidate(TestCase):

    def run(self, path, **kwargs):
        self.output = validate(path=path, **kwargs)

    def test_metadata(self):
        """Test that the generated JSON has the appropriate metadata
        values."""
        self.run('tests/resources/packagelayout/theme.jar')
        j = json.loads(self.output)
        eq_(j['metadata']['name'], 'name_value')
        eq_(j['metadata']['validator_version'], validator.__version__)

    def test_metadata_bundle(self):
        """
        Test that the error bundle returned by validate() has the appropriate
        values within it.
        """
        self.run('tests/resources/packagelayout/theme.jar', format=None)
        eq_(self.output.metadata['name'], 'name_value')

    def test_spidermonkey(self):
        """
        Test that the appropriate path for Spidermonkey is set through the
        `validate()` function.
        """
        self.run('tests/resources/packagelayout/theme.jar', format=None)
        assert self.output.determined
        assert self.output.get_resource('listed')

    def test_undetermined(self):
        """
        Test that when the validation is run with `determined=False`, that
        value is pushed through the full validation process.
        """
        self.run('tests/resources/packagelayout/theme.jar', format=None,
                 determined=False)
        assert not self.output.determined
        assert self.output.get_resource('listed')
        eq_(self.output.metadata['listed'], True)

    def test_unlisted(self):
        """
        Test that when the validation is run with `listed=False`, that value
        is pushed through the full validation process.
        """
        self.run('tests/resources/packagelayout/theme.jar', format=None,
                 listed=False)
        assert self.output.determined
        assert not self.output.get_resource('listed')
        eq_(self.output.metadata['listed'], False)

    def test_overrides(self):
        """
        Test that when the validation is run with `overrides={"foo": "foo"}`,
        that value is pushed through the full validation process.
        """
        self.run('tests/resources/packagelayout/theme.jar', format=None,
                 overrides={'foo': 'foo'})
        assert self.output.determined
        assert self.output.get_resource('listed')
        eq_(self.output.overrides, {'foo': 'foo'})


@patch.dict('validator.constants.APPROVED_APPLICATIONS')
def test_app_versions():
    'Tests that the validate function properly loads app_versions.json'
    validate(path='tests/resources/junk.xpi',
             approved_applications='tests/resources/test_app_versions.json')
    print constants.APPROVED_APPLICATIONS
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
    print constants.APPROVED_APPLICATIONS
    assert constants.APPROVED_APPLICATIONS['1']['name'] == 'Foo App'


def test_is_compat():
    """Test that we know when we're running a compatibility test."""
    out = validate(path='tests/resources/junk.xpi', format=None,
                   compat_test=False)
    assert not out.get_resource('is_compat_test')

    out = validate(path='tests/resources/junk.xpi', format=None,
                   compat_test=True)
    assert out.get_resource('is_compat_test')
