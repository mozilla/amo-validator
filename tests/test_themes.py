import testcases
import testcases.themes
from chromemanifest import ChromeManifest
from helper import _do_test

def test_theme_chrome_manifest():
    "Tests that a theme has a valid chrome manifest file."
    
    _do_test("tests/resources/themes/pass.jar",
             testcases.themes.test_theme_manifest,
             False)

def test_theme_bad_chrome_manifest():
    "Tests that a theme has an invalid chrome manifest file."
    
    _do_test("tests/resources/themes/fail.jar",
             testcases.themes.test_theme_manifest)