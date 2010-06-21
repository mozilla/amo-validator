import testcases
import testcases.langpack
from chromemanifest import ChromeManifest
from errorbundler import ErrorBundle
from helper import _do_test

def test_langpack_valid():
    "Tests that a language pack has a valid chrome manifest file."
    
    _do_test("tests/resources/langpack/pass.xpi",
             testcases.langpack.test_langpack_manifest,
             False)

def test_langpack_bad_subject():
    """Tests that a language pack has an invalid subject in the
    chrome.manifest file."""
    
    _do_test("tests/resources/langpack/fail.xpi",
             testcases.langpack.test_langpack_manifest)

def test_langpack_bad_uri_pred():
    """Tests that a language pack has an invalid URI specified for its
    'override' predicates."""
    
    _do_test("tests/resources/langpack/fail_uri_pred.xpi",
             testcases.langpack.test_langpack_manifest)

def test_langpack_bad_uri_obj():
    """Tests that a language pack has an invalid URI specified for its
    'override' objects."""
    
    _do_test("tests/resources/langpack/fail_uri_obj.xpi",
             testcases.langpack.test_langpack_manifest)

def test_unsafe_html():
    "Tests for unsafe HTML in obstract files."
    
    err = ErrorBundle(None, True)
    
    testcases.langpack.test_unsafe_html(err, None, """
    This is an <b>innocent</b> file.
    Nothing to <a href="#anchor">suspect</a> here.
    <img src="chrome://asdf/locale/asdf" />
    <tag href="#" />""")
    
    assert not err.failed()
    
    testcases.langpack.test_unsafe_html(err, "asdf", """
    This is not an <script>innocent</script> file.""")
    
    assert err.failed()
    
    err = ErrorBundle(None, True)
    testcases.langpack.test_unsafe_html(err, "asdf", """
    Nothing to <a href="http://foo.bar/">suspect</a> here.""")
    
    assert err.failed()
    
    