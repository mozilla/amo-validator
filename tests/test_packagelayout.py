import testcases
import testcases.packagelayout
from helper import _do_test

def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""
    
    _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
             testcases.packagelayout.test_blacklisted_files,
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
    

def test_extra_unimportant():
    """Tests the layout of a theme that contains an unimportant but
    extra directory."""
    
    _do_test("tests/resources/packagelayout/theme_extra_unimportant.jar",
             testcases.packagelayout.test_theme_layout,
             False)
    

def test_extra_whitelisted():
    """Tests the layout of a theme that contains a whitelisted file."""
    
    _do_test("tests/resources/packagelayout/theme_extra_whitelisted.jar",
             testcases.packagelayout.test_theme_layout,
             False)
    


