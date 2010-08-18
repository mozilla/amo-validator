import validator.testcases.markup.csstester as csstester
from validator.errorbundler import ErrorBundle

def _do_test(path, should_fail=False):
    
    css_file = open(path)
    data = css_file.read()
    css_file.close()
    
    err = ErrorBundle(None, True)
    
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
    
def test_css_unicode():
    "Tests that bad unicode is frowned upon."
    
    result = _do_test("tests/resources/markup/csstester/unicode_ewwww.css")
    
    assert result.infos
    
def test_css_webkit():
    "Tests that the scourge of the earth is absent."
    
    _do_test("tests/resources/markup/csstester/webkit.css", True)
    
def test_css_identitybox():
    "Tests that the identity box isn't played with."
    
    _do_test("tests/resources/markup/csstester/identity-box.css", True)