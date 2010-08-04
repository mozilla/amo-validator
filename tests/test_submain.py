import os

import validator.submain as submain
from validator.errorbundler import ErrorBundle
from validator.constants import *

def test_prepare_package():
    "Tests that the prepare_package function passes for valid data"
    
    submain.test_package = lambda w,x,y,z: True
    
    err = ErrorBundle(None, True)
    assert submain.prepare_package(err, "tests/resources/main/foo.xpi") == True
    
def test_prepare_package_missing():
    "Tests that the prepare_package function fails when file is not found"
    
    err = ErrorBundle(None, True)
    submain.prepare_package(err, "foo/bar/asdf/qwerty.xyz")
    
    assert err.failed()
    assert err.reject
    
def test_prepare_package_bad_file():
    "Tests that the prepare_package function fails for unknown files"
    
    err = ErrorBundle(None, True)
    submain.prepare_package(err, "tests/resources/main/foo.bar")
    
    assert err.failed()
    assert err.reject
    
def test_prepare_package_xml():
    "Tests that the prepare_package function passes with search providers"
    
    submain.test_search = lambda err,y,z: True
    
    err = ErrorBundle(None, True)
    submain.prepare_package(err, "tests/resources/main/foo.xml")
    
    assert not err.failed()
    assert not err.reject
    
    submain.test_search = lambda err,y,z: err.error(("x"), "Failed")
    submain.prepare_package(err, "tests/resources/main/foo.xml")
    
    assert err.failed()
    assert err.reject


# Test the function of the decorator iterator

def test_test_inner_package():
    "Tests that the test_inner_package function works properly"
    
    decorator = MockDecorator()
    submain.decorator = decorator
    err = MockErrorHandler(decorator)
    
    submain.test_inner_package(err, "foo", "bar")
    
    assert not err.failed()
    
def test_test_inner_package_failtier():
    "Tests that the test_inner_package function fails at a failed tier"
    
    decorator = MockDecorator(3)
    submain.decorator = decorator
    err = MockErrorHandler(decorator)
    
    submain.test_inner_package(err, "foo", "bar")
    
    assert err.failed()
    
class MockDecorator:
    
    def __init__(self, fail_tier=None):
        self.ordering = [1]
        self.fail_tier = fail_tier
    
    def get_tiers(self):
        "Returns unordered tiers. These must be in a random order."
        return (4, 1, 3, 5, 2)
    
    def get_tests(self, tier, type):
        "Should return a list of tests that occur in a certain order"
        
        self.on_tier = tier
        
        print "Retrieving Tests: Tier %d" % tier
        
        if self.fail_tier is not None:
            if tier == self.fail_tier:
                print "> Fail Tier"
                
                yield {"test":lambda x,y,z: x.fail_tier(),
                       "simple":False}
            
            assert tier <= self.fail_tier
            
        
        for x in range(1,10): # Ten times because we care
            print "Yielding Complex"
            yield {"test":lambda x,y,z: x.report(tier),
                   "simple":False}
            print "Yielding Simple"
            yield {"test":lambda x,y=None,z=None: x.test_simple(y, z),
                   "simple":True}
        
    def report_tier(self, tier):
        "Checks to make sure the last test run is on the current tier."
        
        assert tier == self.on_tier
        
    def report_fail(self):
        "Alerts the tester to a failure"
        
        print self.on_tier
        print self.fail_tier
        assert self.on_tier == self.fail_tier
        
class MockErrorHandler:
    
    def __init__(self, mock_decorator):
        self.decorator = mock_decorator
        self.detected_type = 0
        self.has_failed = False
        
    def report(self, tier):
        "Passes the tier back to the mock decorator to verify the tier"
        self.decorator.report_tier(tier)
        
    def fail_tier(self):
        "Simulates a failure"
        self.has_failed = True
        self.decorator.report_fail()
        
    def test_simple(self, y, z):
        "Makes sure that the second two params of a simple test are respected"
        
        assert y is None
        assert z is None
        
    def failed(self):
        "Simple accessor because the standard error handler has one"
        return self.has_failed