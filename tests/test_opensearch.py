import os

from StringIO import StringIO

import validator.typedetection as typedetection
import validator.submain as submain
from validator.errorbundler import ErrorBundle
from validator.constants import *

def _do_test(url, failure=True):
    
    xml_file = open(url)
    data = xml_file.read()
    wrapper = StringIO(data)
    
    results = typedetection.detect_opensearch(wrapper)
    
    if results["error"]:
        print results["error"]
    
    if failure:
        assert results["failure"]
    else:
        assert not results["failure"]
    
def test_opensearch():
    "Tests that the OpenSearch detection is working."
    
    _do_test("tests/resources/searchprovider/pass.xml", False)
    
def test_nonparsing_xml():
    """Tests that a failure is generated for bad XML on OpenSearch"""
    
    output = typedetection.detect_opensearch("foo/bar/_asdf")
    assert output["failure"]
    
def test_broken_updateURL():
    "Tests that there isn't an updateURL element in the provider."
    
    _do_test("tests/resources/searchprovider/sp_updateurl.xml")
    
def test_broken_notos():
    "Tests that the provider is indeed OpenSearch."
    
    _do_test("tests/resources/searchprovider/sp_notos.xml")
    
def test_broken_shortname():
    "Tests that the provider has a <ShortName> element."
    
    _do_test("tests/resources/searchprovider/sp_no_shortname.xml")
    
def test_broken_description():
    "Tests that the provider has a <Description> element."
    
    _do_test("tests/resources/searchprovider/sp_no_description.xml")
    
def test_broken_url():
    "Tests that the provider has a <Url> element."
    
    _do_test("tests/resources/searchprovider/sp_no_url.xml")

def test_rel_self_url():
    "Tests that the parser skips over rel=self URLs"

    _do_test("tests/resources/searchprovider/rel_self_url.xml", False)
    # It shouldn't fail because it's a "broken" URL that's marked to pass.

def test_broken_url_attributes():
    "Tests that the provider is passing the proper attributes for its urls."
    
    _do_test("tests/resources/searchprovider/sp_bad_url_atts.xml")
    
def test_broken_url_mime():
    "Tests that the provider has a legit MIME on the URL."
    
    _do_test("tests/resources/searchprovider/sp_bad_url_mime.xml")
    
def test_broken_url_searchterms():
    "Tests that a search term field is provided for the <Url> element."
    
    _do_test("tests/resources/searchprovider/sp_no_url_template.xml")
    
def test_broken_url_searchterms_inline():
    "Tests that a valid inline search term field is provided."
    
    _do_test("tests/resources/searchprovider/sp_inline_template.xml", False)
    
def test_broken_url_searchterms_param():
    "Tests that a valid search term field is provided in a <Param />"
    
    _do_test("tests/resources/searchprovider/sp_param_template.xml", False)
    
def test_broken_url_searchterms_param_atts():
    "Tests that necessary attributes are provided in a <Param />"
    
    _do_test("tests/resources/searchprovider/sp_bad_param_atts.xml")
    

def test_search_pass():
    "Tests the submain test_search function with passing data."
    
    err = ErrorBundle(None, True)
    submain.detect_opensearch = lambda x: {"failure":False}
    submain.test_search(err, None, PACKAGE_ANY)
    
    assert not err.failed()
    
def test_search_bad_type():
    "Tests the submain test_search function with a bad package type."
    
    err = ErrorBundle(None, True)
    submain.detect_opensearch = lambda x: {"failure":False}
    submain.test_search(err, None, PACKAGE_THEME)
    
    assert err.failed()
    
def test_search_failure():
    "Tests the submain test_search function with a failure"
    
    err = ErrorBundle(None, True)
    submain.detect_opensearch = lambda x: {"failure":True,
                                           "error":""}
    submain.test_search(err, None, PACKAGE_ANY)
    
    assert err.failed()
    assert err.reject
    
def test_search_failure_undecided():
    "Tests the submain test_search function with an unrejected fail case"
    
    err = ErrorBundle(None, True)
    submain.detect_opensearch = lambda x: {"failure":True,
                                           "error":"",
                                           "decided":False}
    submain.test_search(err, None, PACKAGE_ANY)
    
    assert err.failed()
    assert not err.reject
    
