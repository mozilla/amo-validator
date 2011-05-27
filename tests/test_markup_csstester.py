import validator.testcases.markup.csstester as csstester
from validator.errorbundler import ErrorBundle

def _do_test(path, should_fail=False):

    data = open(path).read()
    err = ErrorBundle()

    csstester.test_css_file(err, "css.css", data)
    err.print_summary(True)

    if should_fail:
        assert err.failed()
    else:
        assert not err.failed()

    return err


def test_css_file():
    "Tests a package with a valid CSS file."

    _do_test("tests/resources/markup/csstester/pass.css")


def test_css_moz_binding():
    "Tests that remote scripts in CSS are blocked."

    _do_test("tests/resources/markup/csstester/mozbinding.css", True)
    _do_test("tests/resources/markup/csstester/mozbinding-pass.css", False)


def test_css_identitybox():
    "Tests that the identity box isn't played with."

    _do_test("tests/resources/markup/csstester/identity-box.css", True)


def test_remote_urls():
    "Tests the Regex used to detect remote URLs"

    t = lambda s:csstester.BAD_URL.match(s) is not None

    assert not t("url(foo/bar.abc)")
    assert not t('url("foo/bar.abc")')
    assert not t("url('foo/bar.abc')")

    assert not t("url(chrome://foo/bar)")
    assert not t("url(resource:asdf)")

    assert t("url(http://abc.def)")
    assert t("url(https://abc.def)")
    assert t("url(ftp://abc.def)")
    assert t("url(//abcdef)")
    assert not t("url(/abc.def)")

    assert not t("UrL(/abc.def)")
    assert t("url(HTTP://foo.bar/)")

