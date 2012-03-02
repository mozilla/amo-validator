import validator.testcases.chromemanifest as tc_chromemanifest
from validator.errorbundler import ErrorBundle
from validator.chromemanifest import ChromeManifest


def test_pass():
    """Test that standard category subjects pass."""

    c = ChromeManifest("category foo bar", "chrome.manifest")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_categories(err)
    assert not err.failed()


def test_no_chromemanifest():
    """
    Chrome manifest tests should not be run if there is no chrome manifest.
    """
    err = ErrorBundle()
    assert tc_chromemanifest.test_categories(err) is None
    assert not err.failed()

    err = ErrorBundle()
    assert tc_chromemanifest.test_resourcemodules(err) is None
    assert not err.failed()


def test_js_categories_gecko2():
    """Test that JS categories raise problems for hyphenated values."""
    c = ChromeManifest("category JavaScript-DOM-class foo bar",
                       "chrome.manifest")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_categories(err)
    assert err.failed()


def test_js_categories_gecko1():
    """Test that JS categories raise problems for space-delimited values."""
    c = ChromeManifest("category JavaScript global foo bar", "chrome.manifest")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_categories(err)
    assert err.failed()


def test_fail_resourcemodules():
    """'resource modules' should fail validation."""
    c = ChromeManifest("resource modules foo", "chrome.manifest")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_resourcemodules(err)
    assert err.failed()

    # Fail even if it's just a prefix.
    c = ChromeManifest("resource modulesfoo", "chrome.manifest")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_resourcemodules(err)
    assert err.failed()


def test_content_instructions():
    """Test that banned content namespaces are banned."""

    err = ErrorBundle()
    c = ChromeManifest("content foo bar", "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    tc_chromemanifest.test_content_instructions(err)
    assert not err.failed()

    c = ChromeManifest("content godlikea bar", "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    tc_chromemanifest.test_content_instructions(err)
    assert err.failed()


def test_content_missing_information():
    """Test that incomplete information in a content instruction fails."""

    err = ErrorBundle()
    c = ChromeManifest("content foo", "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    tc_chromemanifest.test_content_instructions(err)
    assert err.failed()


def test_content_instructions_trailing_slash():
    """Test that trailing slashes are necessary for content instructions."""

    err = ErrorBundle()
    c = ChromeManifest("content namespace /uri/goes/here", "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    tc_chromemanifest.test_content_instructions(err)
    assert not err.failed()
    assert err.notices

    err = ErrorBundle()
    c = ChromeManifest("content namespace /uri/goes/here/ flag=true",
                       "chrome.manifest")
    err.save_resource("chrome.manifest", c)
    tc_chromemanifest.test_content_instructions(err)
    assert not err.failed()
    assert not err.notices

