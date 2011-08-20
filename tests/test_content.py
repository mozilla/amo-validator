from nose.tools import eq_

from helper import MockXPI
from js_helper import _do_test_raw

import validator.xpi as xpi
import validator.testcases.content as content
from validator.errorbundler import ErrorBundle
from validator.chromemanifest import ChromeManifest
from validator.constants import *


def test_xpcnativewrappers():
    "Tests that xpcnativewrappers is not in the chrome.manifest"

    err = ErrorBundle()
    assert content.test_xpcnativewrappers(err, None) is None

    err.save_resource("chrome.manifest",
                      ChromeManifest("foo bar", "chrome.manifest"))
    content.test_xpcnativewrappers(err, None)
    assert not err.failed()

    err.save_resource("chrome.manifest",
                      ChromeManifest("xpcnativewrappers on",
                                     "chrome.manifest"))
    content.test_xpcnativewrappers(err, None)
    assert err.failed()


def test_jar_subpackage():
    "Tests JAR files that are subpackages."

    err = ErrorBundle()
    err.set_type(PACKAGE_EXTENSION)
    err.supported_versions = {"foo": ["1.2.3"]}
    mock_package = MockXPI(
        {"chrome/subpackage.jar":
             "tests/resources/content/subpackage.jar",
         "subpackage.jar":
             "tests/resources/content/subpackage.jar"})

    content.testendpoint_validator = \
        MockTestEndpoint(("test_inner_package", ))

    result = content.test_packed_packages(
                                    err,
                                    mock_package)
    print result
    assert result == 2
    content.testendpoint_validator.assert_expectation(
                                    "test_inner_package",
                                    2)
    content.testendpoint_validator.assert_expectation(
                                    "test_inner_package",
                                    2,
                                    "subpackage")
    assert err.supported_versions == {"foo": ["1.2.3"]}

def test_xpi_subpackage():
    "XPIs should never be subpackages; only nested extensions"

    err = ErrorBundle()
    err.set_type(PACKAGE_EXTENSION)
    mock_package = MockXPI(
        {"chrome/package.xpi":
             "tests/resources/content/subpackage.jar"})

    content.testendpoint_validator = \
        MockTestEndpoint(("test_package", ))

    result = content.test_packed_packages(
        err,
        mock_package)

    print result
    assert result == 1
    content.testendpoint_validator.assert_expectation(
        "test_package",
        1)
    content.testendpoint_validator.assert_expectation(
        "test_package",
        0,
        "subpackage")


def test_xpi_tiererror():
    "Tests that tiers are reset when a subpackage is encountered"

    err = ErrorBundle()
    mock_package = MockXPI(
        {"foo.xpi":
             "tests/resources/content/subpackage.jar"})
    content.testendpoint_validator = MockTestEndpoint(("test_package", ),
                                                      td_error=True)

    err.set_tier(2)
    result = content.test_packed_packages(err,
                                          mock_package)
    assert err.errors[0]["tier"] == 1
    assert err.tier == 2
    assert all(x == 1 for x in content.testendpoint_validator.found_tiers)

def test_jar_nonsubpackage():
    "Tests XPI files that are not subpackages."

    err = ErrorBundle()
    err.set_type(PACKAGE_MULTI)
    err.save_resource("is_multipackage", True)
    mock_package = MockXPI(
        {"foo.jar":
             "tests/resources/content/subpackage.jar",
         "chrome/bar.jar":
             "tests/resources/content/subpackage.jar"})

    content.testendpoint_validator = MockTestEndpoint(("test_inner_package",
                                                       "test_package"))

    result = content.test_packed_packages(
                                    err,
                                    mock_package)
    print result
    assert result == 2
    content.testendpoint_validator.assert_expectation(
                                    "test_package",
                                    2)
    content.testendpoint_validator.assert_expectation(
                                    "test_package",
                                    0,
                                    "subpackage")


def test_markup():
    "Tests markup files in the content validator."

    err = ErrorBundle()
    err.supported_versions = {}
    mock_package = MockXPI({"foo.xml": "tests/resources/content/junk.xpi"})

    tem = content.testendpoint_markup
    content.testendpoint_markup = MockMarkupEndpoint(("process", ))

    result = content.test_packed_packages(
                                    err,
                                    mock_package)
    print result
    assert result == 1
    content.testendpoint_markup.assert_expectation(
                                    "process",
                                    1)
    content.testendpoint_markup.assert_expectation(
                                    "process",
                                    0,
                                    "subpackage")

    content.testendpoint_markup = tem

def test_css():
    "Tests css files in the content validator."

    err = ErrorBundle()
    err.supported_versions = {}
    mock_package = MockXPI({"foo.css": "tests/resources/content/junk.xpi"})

    content.testendpoint_css = MockTestEndpoint(("test_css_file", ))

    result = content.test_packed_packages(err, mock_package)
    print result
    assert result == 1
    content.testendpoint_css.assert_expectation("test_css_file", 1)
    content.testendpoint_css.assert_expectation("test_css_file", 0,
                                                "subpackage")


def test_hidden_files():
    """Tests that hidden files are reported."""

    def test_structure(structure):
        err = ErrorBundle()
        err.supported_versions = {}
        mock_package = MockXPI(structure)
        content.test_packed_packages(err, mock_package)
        print err.print_summary(verbose=True)
        assert err.failed()

    for structure in ({".hidden": "tests/resources/content/junk.xpi"},
                      {"dir/__MACOSX/foo": "tests/resources/content/junk.xpi"},
                      {"dir/.foo.swp": "tests/resources/content/junk.xpi"},
                      {"dir/file.old": "tests/resources/content/junk.xpi"},
                      {"dir/file.xul~": "tests/resources/content/junk.xpi"}):
        yield test_structure, structure


def test_password_in_defaults_prefs():
    """
    Tests that passwords aren't stored in the defaults/preferences/*.js files
    for bug 647109.
    """

    password_js = open("tests/resources/content/password.js").read()
    assert not _do_test_raw(password_js).failed()

    err = ErrorBundle()
    err.supported_versions = {}
    mock_package = MockXPI({"defaults/preferences/foo.js":
                                "tests/resources/content/password.js"})

    content._process_file(err, mock_package, "defaults/preferences/foo.js",
                          password_js, "foo.js")
    print err.print_summary()
    assert err.failed()


def test_langpack():
    "Tests a language pack in the content validator."

    err = ErrorBundle()
    err.supported_versions = {}
    err.set_type(PACKAGE_LANGPACK)
    mock_package = MockXPI({"foo.dtd": "tests/resources/content/junk.xpi"})

    content.testendpoint_langpack = MockTestEndpoint(("test_unsafe_html", ))

    result = content.test_packed_packages(err, mock_package)
    print result
    assert result == 1
    content.testendpoint_langpack.assert_expectation("test_unsafe_html", 1)
    content.testendpoint_langpack.assert_expectation("test_unsafe_html", 0,
                                                     "subpackage")


def test_jar_subpackage_bad():
    "Tests JAR files that are bad subpackages."

    err = ErrorBundle()
    mock_package = MockXPI({"chrome/subpackage.jar":
                            "tests/resources/content/junk.xpi"})

    content.testendpoint_validator = MockTestEndpoint(("test_inner_package", ))

    result = content.test_packed_packages(err, mock_package)
    print result
    assert err.failed()


def test_make_script_absolute():
    """Test that _make_script_absolute() works properly."""

    msa = content._make_script_absolute
    eq_(msa("chrome://a/b.xul", "chrome://foo/bar.js"), "chrome://foo/bar.js")
    eq_(msa("chrome://a/b.xul", "/foo.js"), "chrome://a/foo.js")
    eq_(msa("chrome://a/b/c.xul", "/foo/bar.js"), "chrome://a/foo/bar.js")
    eq_(msa("chrome://a/b/c.xul", "foo.js"), "chrome://a/b/foo.js")
    eq_(msa("chrome://a/b/c.xul", "foo/bar.js"), "chrome://a/b/foo/bar.js")


class MockTestEndpoint(object):
    """
    Simulates a test module and reports whether individual tests have been
    attempted on it.
    """

    def __init__(self, expected, td_error=False):
        expectations = {}
        for expectation in expected:
            expectations[expectation] = {"count": 0,
                                         "subpackage": 0}

        self.expectations = expectations
        self.td_error = td_error
        self.found_tiers = []

    def _tier_test(self, err, xpi, name):
        "A simulated test case for tier errors"
        print "Generating subpackage tier error..."
        self.found_tiers.append(err.tier)
        err.error(("foo", ),
                  "Tier error",
                  "Just a test")

    def __getattribute__(self, name):
        """Detects requests for validation tests and returns an
        object that simulates the outcome of a test."""

        print "Requested: %s" % name

        if name == "test_package" and self.td_error:
            return self._tier_test

        if name in ("expectations",
                    "assert_expectation",
                    "td_error",
                    "_tier_test",
                    "found_tiers"):
            return object.__getattribute__(self, name)

        if name in self.expectations:
            self.expectations[name]["count"] += 1

        if name == "test_package":
            def wrap(package, name, expectation=PACKAGE_ANY):
                pass
        elif name in ("test_css_file", "test_unsafe_html", "process"):
            def wrap(err, name, file_data):
                pass
        else:
            def wrap(err, pak):
                if isinstance(pak, xpi.XPIManager) and pak.subpackage:
                    self.expectations[name]["subpackage"] += 1

        return wrap

    def assert_expectation(self, name, count, type_="count"):
        """Asserts that a particular test has been run a certain number
        of times"""

        print self.expectations
        assert name in self.expectations
        print self.expectations[name][type_]
        assert self.expectations[name][type_] == count


class MockMarkupEndpoint(MockTestEndpoint):
    "Simulates the markup test module"

    def __getattribute__(self, name):

        if name == "MarkupParser":
            return lambda x: self

        return MockTestEndpoint.__getattribute__(self, name)

