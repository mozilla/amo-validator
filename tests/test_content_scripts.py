from nose.tools import eq_

from helper import MockXPI

from validator.chromemanifest import ChromeManifest
import validator.testcases.content as content
from validator.errorbundler import ErrorBundle


def test_packed_scripts_ignored():
    """Test that packed scripts are not tested in subpackages."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    err.save_resource(
        "scripts",
        [{"scripts": ["foo.js"],
          "package": x,
          "state": []}])
    err.package_stack = ["foo"]

    content.test_packed_scripts(err, x)

    assert not err.failed()


def test_packed_scripts_ignored_no_scripts():
    """Test that packed scripts are not tested when there are no scripts."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    content.test_packed_scripts(err, x)
    assert not err.failed()


def test_packed_scripts():
    """Test that packed scripts are tested properly."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    err.save_resource(
        "scripts",
        [{"scripts": ["foo.js"],
          "package": x,
          "state": []}])

    content.test_packed_scripts(err, x)

    assert err.failed()
    assert err.warnings
    assert not err.errors


def test_packed_scripts_regex():
    """Test that packed scripts are tested properly with the regex tests."""

    x = MockXPI({"foo.js": "tests/resources/content/regex_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    err.save_resource(
        "scripts",
        [{"scripts": ["foo.js"],
          "package": x,
          "state": []}])

    content.test_packed_scripts(err, x)

    assert err.failed()
    assert err.warnings
    assert not err.errors


def test_packed_scripts_pollution():
    """Test that packed scripts test for pollution properly."""

    x = MockXPI({"foo/bar.js": "tests/resources/content/pollution_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    c = ChromeManifest("""
    content ns jar:subpackage.jar!/
    """, "chrome.manifest")

    err.save_resource("chrome.manifest_nopush", c, pushable=False)

    err.save_resource(
        "scripts",
        [{"scripts": ["foo/bar.js"],
          "package": x,
          "state": ["subpackage.jar", "subsubpackage"]}])
    err.save_resource("marked_scripts", set(["chrome://ns/foo/bar.js"]))

    content.test_packed_scripts(err, x)

    eq_(err.package_stack, [])

    assert err.failed()
    assert err.warnings
    assert not err.errors

    eq_(err.warnings[0]["file"],
        ['subpackage.jar', 'subsubpackage', 'foo/bar.js'])


def test_packed_scripts_no_pollution():
    """
    Test that packed scripts test for pollution without being overzealous.
    """

    x = MockXPI({"foo/bar.js": "tests/resources/content/pollution_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    c = ChromeManifest("""
    content ns jar:subpackage.jar!/
    """, "chrome.manifest")

    err.save_resource("chrome.manifest_nopush", c, pushable=False)

    err.save_resource(
        "scripts",
        [{"scripts": ["foo/bar.js"],
          "package": x,
          "state": ["subpackage", "subsubpackage"]}])
    err.save_resource("marked_scripts", set(["chrome://otherns/foo/bar.js"]))

    content.test_packed_scripts(err, x)

    eq_(err.package_stack, [])

    assert not err.failed()


