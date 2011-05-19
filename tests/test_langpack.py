import validator.testcases.langpack as langpack
from validator.chromemanifest import ChromeManifest
from validator.errorbundler import ErrorBundle
from helper import _do_test


def test_langpack_valid():
    "Tests that a language pack has a valid chrome manifest file."

    _do_test("tests/resources/langpack/pass.xpi",
             langpack.test_langpack_manifest,
             False)


def test_langpack_bad_subject():
    """Tests that a language pack has an invalid subject in the
    chrome.manifest file."""

    _do_test("tests/resources/langpack/fail.xpi",
             langpack.test_langpack_manifest)


def test_langpack_bad_uri_pred():
    """Tests that a language pack has an invalid URI specified for its
    'override' predicates."""

    _do_test("tests/resources/langpack/fail_uri_pred.xpi",
             langpack.test_langpack_manifest)


def test_langpack_bad_uri_obj():
    """Tests that a language pack has an invalid URI specified for its
    'override' objects."""

    _do_test("tests/resources/langpack/fail_uri_obj.xpi",
             langpack.test_langpack_manifest)


def test_unsafe_html():
    "Tests for unsafe HTML in obstract files."

    err = ErrorBundle(None, True)

    langpack.test_unsafe_html(err, None, """
    This is an <b>innocent</b> file.
    Nothing to <a href="#anchor">suspect</a> here.
    <img src="chrome://asdf/locale/asdf" />
    <tag href="#" />""")

    langpack.test_unsafe_html(err, None, "<tag href='foo' />")

    langpack.test_unsafe_html(err, None, "<tag src='foo' />")
    langpack.test_unsafe_html(err, None, "<tag src='/foo/bar' />")

    assert not err.failed()

    langpack.test_unsafe_html(err, "asdf", """
    This is not an <script>innocent</script> file.""")
    assert err.failed()

    err = ErrorBundle()
    langpack.test_unsafe_html(err, "asdf", """
    Nothing to <a href="http://foo.bar/">suspect</a> here.""")
    assert err.failed()

    err = ErrorBundle()
    langpack.test_unsafe_html(err, "asdf", "src='data:foobar")
    assert err.failed()

    err = ErrorBundle()
    langpack.test_unsafe_html(err, "asdf", "src='//remote/resource")
    assert err.failed()

    err = ErrorBundle()
    langpack.test_unsafe_html(err, "asdf", 'href="ftp://foo.bar/')
    assert err.failed()


def test_has_chrome_manifest():
    """Makes sure the module fails when a chrome.manifest file is not
    available."""

    assert langpack.test_langpack_manifest(ErrorBundle(),
                                           {},
                                           None) is None


def test_valid_chrome_manifest():
    "Chrome manifests must only contain certain elements"

    err = ErrorBundle()
    err.save_resource("chrome.manifest", ChromeManifest("locale foo bar"))
    langpack.test_langpack_manifest(err, {}, None)
    assert not err.failed()

    err.save_resource("chrome.manifest", ChromeManifest("foo bar asdf"))
    langpack.test_langpack_manifest(err, {}, None)
    assert err.failed()

