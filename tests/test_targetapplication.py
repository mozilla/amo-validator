import json
import validator.testcases.targetapplication as targetapp
from validator.constants import *
from validator.errorbundler import ErrorBundle
from helper import _do_test

targetapp.APPROVED_APPLICATIONS = \
        json.load(open("validator/app_versions.json"))

def test_valid_targetapps():
    """Tests that the install.rdf contains only valid entries for
    target applications."""
    
    print targetapp.APPROVED_APPLICATIONS

    _do_test("tests/resources/targetapplication/pass.xpi",
             targetapp.test_targetedapplications,
             False,
             True)

def test_ta_seamonkey():
    """Tests that files that list SeaMonkey support include the
    mandatory install.js file."""
    
    err = _do_test(
            "tests/resources/targetapplication/bad_seamonkey.xpi",
            targetapp.test_targetedapplications,
            True,
            True)
    
    assert not err.reject

def test_ta_seamonkey_dict():
    """Tests that SeaMonkey support is mandatory for dictionary
    packages."""
    
    err = _do_test(
            "tests/resources/targetapplication/bad_seamonkey.xpi",
            targetapp.test_targetedapplications,
            True,
            True,
            PACKAGE_DICTIONARY)
    
    assert err.reject

def test_bad_min_max():
    """Tests that the lower/upper-bound version number for a
    targetApplication entry is indeed a valid version number"""
    
    _do_test("tests/resources/targetapplication/bad_min.xpi",
             targetapp.test_targetedapplications,
             True,
             True)
             
    _do_test("tests/resources/targetapplication/bad_max.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

def test_bad_order():
    """Tests that the min and max versions are ordered correctly such
    that the earlier version is the min and vice-versa."""
    
    _do_test("tests/resources/targetapplication/bad_order.xpi",
             targetapp.test_targetedapplications,
             True,
             True)
             
def test_dup_targets():
    """Tests that there are no duplicate targetAppication elements."""
    
    _do_test("tests/resources/targetapplication/dup_targapp.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

def test_has_installrdfs():
    """Tests that install.rdf files are present."""
    
    err = ErrorBundle(None, True)
    
    # Test package to make sure has_install_rdf is set to True.
    assert targetapp.test_targetedapplications(err, {}, None) is None

def test_is_ff4():
    """Tests a passing install.rdf package for whether it's built for
    Firefox 4. This doesn't pass or fail a package, but it is used for
    other tests in other modules in higher tiers."""
    
    results = _do_test("tests/resources/targetapplication/ff4.xpi",
                       targetapp.test_targetedapplications,
                       False,
                       True)
    
    assert results.get_resource("ff4")
