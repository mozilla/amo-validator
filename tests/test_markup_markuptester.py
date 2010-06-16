import testcases
import testcases.markup
import testcases.markup.markuptester
from errorbundler import ErrorBundle

def _do_test(path, should_fail=False):
    
    markup_file = open(path)
    data = markup_file.read()
    markup_file.close()
    
    filename = path.split("/")[-1]
    extension = filename.split(".")[-1]
    
    err = ErrorBundle(None, True)
    
    parser = testcases.markup.markuptester.MarkupParser(err)
    parser.process(filename, data, extension)
    
    err.print_summary(True)
    
    if should_fail:
        assert err.failed()
    else:
        assert not err.failed()
    
    return err
    

def test_html_file():
    "Tests a package with a valid HTML file."
    
    _do_test("tests/resources/markup/markuptester/pass.html")
    
def test_xml_file():
    "Tests a package with a valid XML file."
    
    _do_test("tests/resources/markup/markuptester/pass.xml")
    

def test_xml_bad_nesting():
    "Tests an XML file that has badly nested elements."
    
    _do_test("tests/resources/markup/markuptester/bad_nesting.xml",
             True)
    
def test_xml_overclosing():
    "Tests an XML file that has overclosed elements"
    
    _do_test("tests/resources/markup/markuptester/overclose.xml",
             True)
    
def test_xml_extraclosing():
    "Tests an XML file that has extraclosed elements"
    
    _do_test("tests/resources/markup/markuptester/extraclose.xml",
             True)
    
def test_html_ignore_comment():
    "Tests that HTML comment values are ignored"
    
    err = _do_test(
            "tests/resources/markup/markuptester/ignore_comments.html")
    