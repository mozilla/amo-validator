import testcases.l10ncompleteness as l10n
from errorbundler import ErrorBundle
from helper import _do_test
from constants import *

def test_pass():
    "Test a package with localization that should pass validation."
    
    _do_test("tests/resources/l10n/lp_pass.xpi",
             l10n.test_xpi,
             failure=False,
             set_type=PACKAGE_EXTENSION)

def test_chromemanifest():
    "Make sure it only accepts packs with chrome.manifest files."
    
    assert l10n.test_lp_xpi(None, {}, None) is None
    
