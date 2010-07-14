import validator.testcases.l10ncompleteness as l10n
from validator.errorbundler import ErrorBundle
from helper import _do_test
from validator.constants import *

def test_pass():
    "Test a package with localization that should pass validation."
    
    _do_test("tests/resources/l10n/pass.xpi",
             l10n.test_xpi,
             failure=False,
             set_type=PACKAGE_EXTENSION)

def test_unlocalizable():
    "Test a package without localization data."
    
    _do_test("tests/resources/l10n/unlocalizable.xpi",
             l10n.test_xpi,
             failure=False,
             set_type=PACKAGE_EXTENSION)

def test_missing():
    "Test a package with missing localization entities."
    
    _do_test("tests/resources/l10n/l10n_incomplete.xpi",
             l10n.test_xpi,
             set_type=PACKAGE_EXTENSION)

def test_missingfiles():
    "Test a package with missing localization files."
    
    _do_test("tests/resources/l10n/l10n_missingfiles.xpi",
             l10n.test_xpi,
             set_type=PACKAGE_EXTENSION)

def test_unmodified():
    """Test a package containing localization entities that have been
    unmodified from the reference locale (en-US)"""
    
    _do_test("tests/resources/l10n/l10n_unmodified.xpi",
             l10n.test_xpi,
             set_type=PACKAGE_EXTENSION)
    

def test_subpackage():
    "Test a package with localization that should pass validation."
    
    err = ErrorBundle(None, True)
    err.set_type(PACKAGE_DICTIONARY)
    assert l10n.test_xpi(err, {}, None) is None
    err.set_type(PACKAGE_EXTENSION)
    err.push_state()
    assert l10n.test_xpi(err, {}, None) is None
    

