from nose.tools import eq_

from helper import MockXPI

from validator.chromemanifest import ChromeManifest
import validator.testcases.content as content
from validator.errorbundler import ErrorBundle


def test_marking_overlays():
    """
    Mark an overlay, then test that it marks the scripts within the overlay.
    """

    err = ErrorBundle()
    err.supported_versions = {}
    c = ChromeManifest("""
    content ns1 foo/
    overlay chrome://foo chrome://ns1/content/main.xul
    """, "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    err.save_resource("chrome.manifest_nopush", c)

    xpi = MockXPI({"foo/main.xul": "tests/resources/content/script_list.xul"})

    content.test_packed_packages(err, xpi)
    assert not err.failed()

    marked_scripts = err.get_resource("marked_scripts")
    print marked_scripts
    assert marked_scripts

    eq_(marked_scripts, set(["chrome://ns1/foo.js",
                             "chrome://ns1/bar.js",
                             "chrome://asdf/foo.js"]))


def test_marking_overlays_no_overlay():
    """
    Test that unmarked overlays don't mark scripts as being potentially
    pollutable.
    """

    err = ErrorBundle()
    err.supported_versions = {}
    c = ChromeManifest("""
    content ns1 foo/
    #overlay chrome://foo chrome://ns1/main.xul
    """, "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    err.save_resource("chrome.manifest_nopush", c)

    xpi = MockXPI({"foo/main.xul": "tests/resources/content/script_list.xul"})

    content.test_packed_packages(err, xpi)
    assert not err.failed()

    marked_scripts = err.get_resource("marked_scripts")
    print marked_scripts
    assert not marked_scripts


def test_marking_overlays_subdir():
    """
    Mark an overlay in a subdirectory, then test that it marks the scripts
    within the overlay. Make sure it properly figures out relative URLs.
    """

    err = ErrorBundle()
    err.supported_versions = {}
    c = ChromeManifest("""
    content ns1 foo/
    overlay chrome://foo chrome://ns1/content/subdir/main.xul
    """, "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    err.save_resource("chrome.manifest_nopush", c)

    xpi = MockXPI({"foo/subdir/main.xul":
                       "tests/resources/content/script_list.xul"})

    content.test_packed_packages(err, xpi)
    assert not err.failed()

    marked_scripts = err.get_resource("marked_scripts")
    print marked_scripts
    assert marked_scripts

    eq_(marked_scripts, set(["chrome://ns1/subdir/foo.js", "chrome://ns1/bar.js",
                             "chrome://asdf/foo.js"]))


def test_script_scraping():
    """Test that scripts are gathered up during the validation process."""

    err = ErrorBundle()
    err.supported_versions = {}
    xpi = MockXPI({"foo.js": "tests/resources/junk.xpi",
                   "dir/bar.jsm": "tests/resources/junk.xpi"})

    content.test_packed_packages(err, xpi)
    assert not err.failed()

    scripts = err.get_resource("scripts")
    print scripts
    assert scripts

    for bundle in scripts:
        assert "foo.js" in bundle["scripts"]
        assert "dir/bar.jsm" in bundle["scripts"]
        eq_(bundle["package"], xpi)
        eq_(bundle["state"], [])

