import testcases
import testcases.targetapplication as targetapp
from constants import *
from errorbundler import ErrorBundle
from helper import _do_test

def test_valid_targetapps():
    """Tests that the install.rdf contains only valid entries for
    target applications."""
    
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

