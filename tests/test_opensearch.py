import os

import typedetection
from StringIO import StringIO

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
    
    _do_test("tests/resources/searchprovider/search_provider.xml", False)
    
def test_broken_updateURL():
    "Tests that there isn't an updateURL element in the provider."
    
    _do_test("tests/resources/searchprovider/search_provider_updateurl.xml")
    
def test_broken_notos():
    "Tests that the provider is indeed OpenSearch."
    
    _do_test("tests/resources/searchprovider/search_provider_notos.xml")
    
def test_broken_shortname():
    "Tests that the provider has a <ShortName> element."
    
    _do_test("tests/resources/searchprovider/search_provider_shortname.xml")
    
def test_broken_description():
    "Tests that the provider has a <Description> element."
    
    _do_test("tests/resources/searchprovider/search_provider_description.xml")
    
def test_broken_url():
    "Tests that the provider has a <Url> element."
    
    _do_test("tests/resources/searchprovider/search_provider_url.xml")
    
def test_broken_url_mime():
    "Tests that the provider has a legit MIME on the URL."
    
    _do_test("tests/resources/searchprovider/search_provider_url_mime.xml")
    
def test_broken_url_searchterms():
    "Tests that a search term field is provided for the <Url> element."
    
    _do_test("tests/resources/searchprovider/search_provider_url_term.xml")
    
def test_broken_url_searchterms_inline():
    "Tests that a valid inline search term field is provided."
    
    _do_test("tests/resources/searchprovider/search_provider_url_term2.xml", False)
    
def test_broken_url_searchterms_param():
    "Tests that a valid search term field is provided in a <Param />"
    
    _do_test("tests/resources/searchprovider/search_provider_url_term3.xml", False)
    
