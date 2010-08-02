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