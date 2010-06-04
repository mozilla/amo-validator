import os

import decorator
import testcases
import testcases.packagelayout
from errorbundler import ErrorBundle
from xpi import XPIManager
from rdf import RDFParser

def _do_test(path, test, failure=True, require_install=False, set_type=0):
    
    package_data = open(path)
    package = XPIManager(package_data, path)
    contents = package.get_file_data()
    err = ErrorBundle(None, True)
    
    
    
    # Populate in the dependencies.
    if set_type:
        err.set_type(1) # Conduit test requires type
    if require_install:
        err.save_resource("has_install_rdf", True)
        rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(rdf_data)
        err.save_resource("install_rdf", install_rdf)
    
    test(err, contents, package)
    
    err.print_summary()
    
    if failure:
        assert err.failed()
    else:
        assert not err.failed()

def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""
    
    _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
             testcases.packagelayout.test_blacklisted_files,
             True)
    


def test_ta_seamonkey():
    """Tests that files that list SeaMonkey support include the
    mandatory install.js file."""
    
    _do_test("tests/resources/packagelayout/bad_seamonkey.xpi",
             testcases.packagelayout.test_targetedapplications,
             True,
             True)
    

# Showing that the layout inspector works for one addon type proves
# that it works for all other addon types (they use the same function
# to do all of the heavy lifting).

def test_layout_passing():
    "Tests the layout of a proper theme"
    
    _do_test("tests/resources/packagelayout/theme.jar",
             testcases.packagelayout.test_theme_layout,
             False)
    

def test_layout_missing_mandatory():
    "Tests the layout of a theme that's missing its chrome/*.jar"
    
    _do_test("tests/resources/packagelayout/theme_nojar.jar",
             testcases.packagelayout.test_theme_layout,
             True)
    

def test_layout_missing_extra_unimportant():
    """Tests the layout of a theme that contains an unimportant but
    extra directory."""
    
    _do_test("tests/resources/packagelayout/theme_extra_unimportant.jar",
             testcases.packagelayout.test_theme_layout,
             False)
    

def test_layout_missing_extra_whitelisted():
    """Tests the layout of a theme that contains a whitelisted file."""
    
    _do_test("tests/resources/packagelayout/theme_extra_whitelisted.jar",
             testcases.packagelayout.test_theme_layout,
             False)
    


