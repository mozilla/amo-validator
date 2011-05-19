import validator.testcases.chromemanifest as tc_chromemanifest
from validator.errorbundler import ErrorBundle
from validator.chromemanifest import ChromeManifest


def test_pass():
    """Test that standard category subjects pass."""

    c = ChromeManifest("category foo bar")
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


def test_js_categories_gecko2():
    """Test that JS categories raise problems for hyphenated values."""
    c = ChromeManifest("category JavaScript-DOM-class foo bar")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_categories(err)
    assert err.failed()


def test_js_categories_gecko1():
    """Test that JS categories raise problems for space-delimited values."""
    c = ChromeManifest("category JavaScript global foo bar")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_categories(err)
    assert err.failed()


def test_fail_resourcemodules():
    """'resource modules' should fail validation."""
    c = ChromeManifest("resource modules foo")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_resourcemodules(err)
    assert err.failed()

    # Fail even if it's just a prefix.
    c = ChromeManifest("resource modulesfoo")
    err = ErrorBundle()
    err.save_resource("chrome.manifest", c)

    tc_chromemanifest.test_resourcemodules(err)
    assert err.failed()

