import os

from StringIO import StringIO

import validator.xpi as xpi
import validator.testcases.content as content
from validator.errorbundler import ErrorBundle
from helper import _do_test
from validator.constants import *

def test_ignore_macstuff():
    "Tests that the content manager will ignore Mac-generated files"
    
    err = ErrorBundle(None, True)
    result = content.test_packed_packages(err,
                                          {"__MACOSX": None,
                                           "__MACOSX/foo": None,
                                           "__MACOSX/bar": None,
                                           "__MACOSX/.DS_Store": None,
                                           ".DS_Store": None},
                                          None)
    assert result == 0

def test_jar_subpackage():
    "Tests JAR files that are subpackages."
    
    err = ErrorBundle(None, True)
    mock_package = MockXPIManager(
        {"chrome/subpackage.jar":
             "tests/resources/content/subpackage.jar",
         "nonsubpackage.jar":
             "tests/resources/content/subpackage.jar"})
                        
    content.testendpoint_validator = \
        MockTestEndpoint(("test_inner_package", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"chrome/subpackage.jar":
                                      {"extension": "jar",
                                       "name_lower": "subpackage.jar"},
                                     "nonsubpackage.jar":
                                      {"extension": "jar",
                                       "name_lower": "subpackage.jar"},
                                       },
                                    mock_package)
    print result
    assert result == 2
    content.testendpoint_validator.assert_expectation(
                                    "test_inner_package",
                                    2)
    content.testendpoint_validator.assert_expectation(
                                    "test_inner_package",
                                    1,
                                    "subpackage")
    

def test_xpi_nonsubpackage():
    "Tests XPI files that are not subpackages."
    
    err = ErrorBundle(None, True)
    mock_package = MockXPIManager(
        {"foo.xpi":
             "tests/resources/content/subpackage.jar"})
                        
    content.testendpoint_validator = \
        MockTestEndpoint(("test_package", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"foo.xpi":
                                      {"extension": "xpi",
                                       "name_lower": "foo.xpi"}},
                                    mock_package)
    print result
    assert result == 1
    content.testendpoint_validator.assert_expectation(
                                    "test_package",
                                    1)
    content.testendpoint_validator.assert_expectation(
                                    "test_package",
                                    0,
                                    "subpackage")
    

def test_markup():
    "Tests markup files in the content validator."
    
    err = ErrorBundle(None, True)
    mock_package = MockXPIManager(
        {"foo.xml":
             "tests/resources/content/junk.xpi"})
                        
    content.testendpoint_markup = \
        MockMarkupEndpoint(("process", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"foo.xml":
                                      {"extension": "xml",
                                       "name_lower": "foo.xml"}},
                                    mock_package)
    print result
    assert result == 1
    content.testendpoint_markup.assert_expectation(
                                    "process",
                                    1)
    content.testendpoint_markup.assert_expectation(
                                    "process",
                                    0,
                                    "subpackage")
    
def test_css():
    "Tests css files in the content validator."
    
    err = ErrorBundle(None, True)
    mock_package = MockXPIManager(
        {"foo.css":
             "tests/resources/content/junk.xpi"})
                        
    content.testendpoint_css = \
        MockTestEndpoint(("test_css_file", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"foo.css":
                                      {"extension": "css",
                                       "name_lower": "foo.css"}},
                                    mock_package)
    print result
    assert result == 1
    content.testendpoint_css.assert_expectation(
                                    "test_css_file",
                                    1)
    content.testendpoint_css.assert_expectation(
                                    "test_css_file",
                                    0,
                                    "subpackage")
    

def test_langpack():
    "Tests a language pack in the content validator."
    
    err = ErrorBundle(None, True)
    err.set_type(PACKAGE_LANGPACK)
    mock_package = MockXPIManager(
        {"foo.dtd":
             "tests/resources/content/junk.xpi"})
                        
    content.testendpoint_langpack = \
        MockTestEndpoint(("test_unsafe_html", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"foo.dtd":
                                      {"extension": "dtd",
                                       "name_lower": "foo.dtd"}},
                                    mock_package)
    print result
    assert result == 1
    content.testendpoint_langpack.assert_expectation(
                                    "test_unsafe_html",
                                    1)
    content.testendpoint_langpack.assert_expectation(
                                    "test_unsafe_html",
                                    0,
                                    "subpackage")
    

def test_jar_subpackage_bad():
    "Tests JAR files that are bad subpackages."
    
    err = ErrorBundle(None, True)
    mock_package = MockXPIManager({"chrome/subpackage.jar":
                            "tests/resources/content/junk.xpi"})
                        
    content.testendpoint_validator = \
        MockTestEndpoint(("test_inner_package", ))
    
    result = content.test_packed_packages(
                                    err,
                                    {"chrome/subpackage.jar":
                                      {"extension": "jar",
                                       "name_lower":
                                           "subpackage_bad.jar"}},
                                    mock_package)
    print result
    assert err.failed()
    

class MockTestEndpoint(object):
    """Simulates a test module and reports whether individual tests
    have been attempted on it."""
    
    def __init__(self, expected):
        expectations = {}
        
        for expectation in expected:
            expectations[expectation] = {"count": 0,
                                         "subpackage": 0}
        
        self.expectations = expectations
        
    def __getattribute__(self, name):
        """"Detects requests for validation tests and returns an
        object that simulates the outcome of a test."""
        
        print "Requested: %s" % name
        
        if name in ("expectations",
                    "assert_expectation"):
            return object.__getattribute__(self, name)
        
        if name in self.expectations:
            self.expectations[name]["count"] += 1
        
        if name == "test_package":
            def wrap(package, name, expectation=PACKAGE_ANY):
                pass
        else:
            def wrap(err, con, pak):
                if isinstance(pak, xpi.XPIManager) and pak.subpackage:
                    self.expectations[name]["subpackage"] += 1
        
        return wrap
        
    def assert_expectation(self, name, count, type_="count"):
        """Asserts that a particular test has been run a certain number
        of times"""
        
        print self.expectations
        assert name in self.expectations
        print self.expectations[name][type_]
        assert self.expectations[name][type_] == count
        

class MockMarkupEndpoint(MockTestEndpoint):
    "Simulates the markup test module"
    
    def __getattribute__(self, name):
        
        if name == "MarkupParser":
            return lambda x: self
        
        return MockTestEndpoint.__getattribute__(self, name)
        

class MockXPIManager(object):
    """Simulates an XPIManager object to make it much easier to test
    packages and their contents"""
    
    def __init__(self, package_contents):
        self.contents = package_contents
    
    def test(self):
        "Simulate an integrity check. Just return true."
        return True
    
    def read(self, filename):
        "Simulates an unpack-to-memory operation."
        
        prelim_resource = self.contents[filename]
        
        if isinstance(prelim_resource, str):
            
            resource = open(prelim_resource)
            data = resource.read()
            resource.close()
        
            return data
        
    
