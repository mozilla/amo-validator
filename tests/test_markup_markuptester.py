import validator.testcases.markup.markuptester as markuptester
from validator.errorbundler import ErrorBundle
from validator.constants import *

def _do_test(path, should_fail=False, type_=None):
    
    markup_file = open(path)
    data = markup_file.read()
    markup_file.close()
    
    filename = path.split("/")[-1]
    extension = filename.split(".")[-1]
    
    err = ErrorBundle(None, True)
    if type_:
        err.set_type(type_)
    
    parser = markuptester.MarkupParser(err, True)
    parser.process(filename, data, extension)
    
    err.print_summary(True)
    
    if should_fail:
        assert err.failed()
    else:
        assert not err.failed()
    
    return err
    

def test_local_url_detector():
    "Tests that local URLs can be detected."
    
    err = ErrorBundle(None, True)
    mp = markuptester.MarkupParser(err)
    tester = mp._is_url_local
    
    assert tester("chrome://xyz/content/abc")
    assert tester("chrome://whatever/")
    assert tester("local.xul")
    assert not tester("http://foo.bar/")
    assert not tester("https://abc.def/")
    

def test_html_file():
    "Tests a package with a valid HTML file."
    
    _do_test("tests/resources/markup/markuptester/pass.html")
    
def test_xml_file():
    "Tests a package with a valid XML file."
    
    _do_test("tests/resources/markup/markuptester/pass.xml")
    
def test_xul_file():
    "Tests a package with a valid XUL file."
    
    _do_test("tests/resources/markup/markuptester/pass.xul")
    
def test_xml_bad_nesting():
    "Tests an XML file that has badly nested elements."
    
    _do_test("tests/resources/markup/markuptester/bad_nesting.xml", True)
    
def test_has_cdata():
    "Tests that CDATA is good to go."
    
    _do_test("tests/resources/markup/markuptester/cdata.xml")
    
def test_xml_overclosing():
    "Tests an XML file that has overclosed elements"
    
    _do_test("tests/resources/markup/markuptester/overclose.xml", True)
    
def test_xml_extraclosing():
    "Tests an XML file that has extraclosed elements"
    
    _do_test("tests/resources/markup/markuptester/extraclose.xml", True)
    
def test_html_ignore_comment():
    "Tests that HTML comment values are ignored"
    
    _do_test("tests/resources/markup/markuptester/ignore_comments.html")
    
def test_html_css_style():
    "Tests that CSS within an element is passed to the CSS tester"
    
    _do_test("tests/resources/markup/markuptester/css_style.html", True)
    
def test_html_css_inline():
    "Tests that inline CSS is passed to the CSS tester"
    
    _do_test("tests/resources/markup/markuptester/css_inline.html", True)
    
def test_xul_evil():
    "Tests for evil kinds of scripts and iframes in XUL."
    
    _do_test("tests/resources/markup/markuptester/remote_src.xul", True)
    
    _do_test("tests/resources/markup/markuptester/bad_iframe_remote.xul", True)
    _do_test("tests/resources/markup/markuptester/bad_iframe_chrome.xul", True)
    _do_test("tests/resources/markup/markuptester/"
             "bad_iframe_remote_missing.xul",
             True)
    
def test_lp_passing():
    "Tests a valid language pack file."
    
    _do_test("tests/resources/markup/markuptester/_langpack/lp_safe.html",
             False,
             PACKAGE_LANGPACK)
    
def test_lp_unsafe():
    "Tests a language pack file that contains unsafe elements."
    
    _do_test("tests/resources/markup/markuptester/_langpack/lp_unsafe.html",
             True,
             PACKAGE_LANGPACK)
    
def test_lp_remote():
    "Tests a language pack file that contains remote references."
    
    _do_test("tests/resources/markup/markuptester/_langpack/lp_remote.html",
             True,
             PACKAGE_LANGPACK)
    
def test_invalid_markup():
    "Tests an markup file that is simply broken."
    
    # Test for the banned test element
    _do_test("tests/resources/markup/markuptester/bad_banned.xml", True)
    
    result = _do_test("tests/resources/markup/markuptester/bad.xml", True)
    assert result.warnings
    result = _do_test("tests/resources/markup/markuptester/bad_script.xml",
                      False)
    assert result.infos
