import json

from mock import patch
from nose.tools import eq_

from validator.validate import validate, validate_app
from validator.errorbundler import ErrorBundle
import validator.constants as constants
from validator.constants import PACKAGE_WEBAPP

from helper import TestCase


class TestValidate(TestCase):

    def run(self, path, **kwargs):
        self.output = validate(path=path, **kwargs)

    def test_metadata(self):
        """Test that the generated JSON has the appropriate metadata valuees."""
        self.run("tests/resources/packagelayout/theme.jar")
        j = json.loads(self.output)
        eq_(j["metadata"]["name"], "name_value")

    def test_metadata_bundle(self):
        """
        Test that the error bundle returned by validate() has the appropriate
        values within it.
        """
        self.run("tests/resources/packagelayout/theme.jar", format=None)
        eq_(self.output.metadata["name"], "name_value")
        eq_(self.output.get_resource("SPIDERMONKEY"), False)

    def test_spidermonkey(self):
        """
        Test that the appropriate path for Spidermonkey is set through the
        `validate()` function.
        """
        self.run("tests/resources/packagelayout/theme.jar", format=None,
                 spidermonkey="foospidermonkey")
        eq_(self.output.get_resource("SPIDERMONKEY"), "foospidermonkey")
        assert self.output.determined
        assert self.output.get_resource("listed")

    def test_undetermined(self):
        """
        Test that when the validation is run with `determined=False`, that
        value is pushed through the full validation process.
        """
        self.run("tests/resources/packagelayout/theme.jar", format=None,
                 determined=False)
        assert not self.output.determined
        assert self.output.get_resource("listed")

    def test_unlisted(self):
        """
        Test that when the validation is run with `listed=False`, that value
        is pushed through the full validation process.
        """
        self.run("tests/resources/packagelayout/theme.jar", format=None,
                 listed=False)
        assert self.output.determined
        assert not self.output.get_resource("listed")

    def test_overrides(self):
        """
        Test that when the validation is run with `overrides="foo"`, that value
        is pushed through the full validation process.
        """
        self.run("tests/resources/packagelayout/theme.jar", format=None,
                 overrides="foo")
        assert self.output.determined
        assert self.output.get_resource("listed")
        eq_(self.output.overrides, "foo")


@patch.dict("validator.constants.APPROVED_APPLICATIONS")
def test_app_versions():
    "Tests that the validate function properly loads app_versions.json"
    validate(path="tests/resources/junk.xpi",
             approved_applications="tests/resources/test_app_versions.json")
    print constants.APPROVED_APPLICATIONS
    assert constants.APPROVED_APPLICATIONS["1"]["name"] == "Foo App"


@patch.dict("validator.constants.APPROVED_APPLICATIONS")
def test_app_versions_dict():
    """
    Test that `approved_applications` can be provided as a pre-parsed dict
    of versions.
    """
    with open("tests/resources/test_app_versions.json") as f:
        apps = json.load(f)
    validate(path="tests/resources/junk.xpi", approved_applications=apps)
    print constants.APPROVED_APPLICATIONS
    assert constants.APPROVED_APPLICATIONS["1"]["name"] == "Foo App"


def test_mrkt_urls():
    """
    Tests that Marketplace URLs are correctly added to the MRKT_URLS constant.
    """
    # Keep a copy so we don't permanently overwrite.
    MRKT_URLS = constants.DEFAULT_WEBAPP_MRKT_URLS[:]

    validate(path="tests/resources/junk.xpi",
             market_urls=["foobar"])
    print constants.DEFAULT_WEBAPP_MRKT_URLS
    assert "foobar" in constants.DEFAULT_WEBAPP_MRKT_URLS

    # Clean up!
    constants.DEFAULT_WEBAPP_MRKT_URLS = MRKT_URLS


def test_is_compat():
    """Test that we know when we're running a compatibility test."""
    out = validate(path="tests/resources/junk.xpi", format=None,
                   compat_test=False)
    assert not out.get_resource("is_compat_test")

    out = validate(path="tests/resources/junk.xpi", format=None,
                   compat_test=True)
    assert out.get_resource("is_compat_test")


def test_webapp():
    """Test that webapps can be validated traditionally."""
    out = validate(path="tests/resources/testwebapp.webapp",
                   expectation=PACKAGE_WEBAPP)
    j = json.loads(out)
    assert j["success"], "Expected not to fail"


def test_webapp_new():
    """Test that webapps can be validated with the new api."""
    with open("tests/resources/testwebapp.webapp") as file_:
        out = validate_app(file_.read())
    j = json.loads(out)
    assert j["success"], "Expected not to fail"

