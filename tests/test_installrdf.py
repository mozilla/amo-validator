import validator.testcases.installrdf as installrdf
from validator.errorbundler import ErrorBundle
from validator.rdf import RDFParser
from helper import _do_test
from validator.constants import *

def _test_value(value, test, failure=True):
    "Tests a value against a test."
    
    err = ErrorBundle(None, True)
    
    test(err, value)
    
    if failure:
        return err.failed()
    else:
        return not err.failed()

def test_pass_id():
    "Tests that valid IDs will be accepted."
    
    _test_value("{12345678-1234-1234-1234-123456789012}",
                installrdf._test_id,
                False)
    _test_value("abc@foo.bar",
                installrdf._test_id,
                False)
    _test_value("a+bc@foo.bar",
                installrdf._test_id,
                False)
    
def test_fail_id():
    "Tests that invalid IDs will not be accepted."
    
    _test_value("{1234567-1234-1234-1234-123456789012}",
                installrdf._test_id)
    _test_value("!@foo.bar",
                installrdf._test_id)
    
def test_pass_version():
    "Tests that valid versions will be accepted."
    
    _test_value("1.2.3.4",
                installrdf._test_version,
                False)
    _test_value("1a.2+.3b",
                installrdf._test_version,
                False)
    
def test_fail_version():
    "Tests that invalid versions will not be accepted."
    
    _test_value("2.0 alpha", installrdf._test_version)
    _test_value("whatever", installrdf._test_version)
    
def test_pass_name():
    "Tests that valid names will be accepted."
    
    _test_value("Joe Schmoe's Feed Aggregator",
                installrdf._test_name,
                False)
    _test_value("Ozilla of the M",
                installrdf._test_name,
                False)
    
def test_fail_name():
    "Tests that invalid names will not be accepted."
    
    _test_value("Love of the Firefox", installrdf._test_name)
    _test_value("Mozilla Feed Aggregator", installrdf._test_name)

def _run_test(filename, failure=True, detected_type=None):
    "Runs a test on an install.rdf file"
    
    err = ErrorBundle(None, True)
    err.detected_type = detected_type
    
    file_ = open(filename)
    data = file_.read()
    file_.close()
    
    parser = RDFParser(data)
    installrdf._test_rdf(err, parser)
    
    if failure: # pragma: no cover
        assert err.failed()
    else:
        assert not err.failed()
    
    return err

def test_has_rdf():
    "Tests that tests won't be run if there's no install.rdf"
    
    err = ErrorBundle(None, True)
    err.save_resource("install_rdf", "test")
    err.save_resource("has_install_rdf", True)
    testrdf = installrdf._test_rdf
    installrdf._test_rdf = lambda x, y: y
    
    result = installrdf.test_install_rdf_params(err, None, None)
    installrdf._test_rdf = testrdf
    
    print result
    assert result
    

def test_passing():
    "Tests a passing install.rdf package."
    
    _run_test("tests/resources/installrdf/pass.rdf", False)

def test_must_exist_once():
    "Tests that elements that must exist once only exist once."
    
    _run_test("tests/resources/installrdf/must_exist_once_missing.rdf")
    _run_test("tests/resources/installrdf/must_exist_once_extra.rdf")

def test_may_exist_once():
    "Tests that elements that may exist once only exist up to once."
    
    _run_test("tests/resources/installrdf/may_exist_once_missing.rdf",
              False)
    _run_test("tests/resources/installrdf/may_exist_once_extra.rdf")

def test_may_exist_once_theme():
    "Tests that elements that may exist once in themes."
    
    _run_test("tests/resources/installrdf/may_exist_once_theme.rdf",
              False,
              PACKAGE_THEME)
    _run_test("tests/resources/installrdf/may_exist_once_theme_fail.rdf",
              True,
              PACKAGE_THEME)
    _run_test("tests/resources/installrdf/may_exist_once_extra.rdf",
              True,
              PACKAGE_THEME)

def test_may_exist():
    "Tests that elements that may exist once only exist up to once."
    
    _run_test("tests/resources/installrdf/may_exist_missing.rdf",
              False)
    _run_test("tests/resources/installrdf/may_exist_extra.rdf", False)

def test_mustmay_exist():
    "Tests that elements that may exist once only exist up to once."
    
    # The first part of this is proven by test_must_exist_once
    
    _run_test("tests/resources/installrdf/mustmay_exist_extra.rdf",
              False)

def test_shouldnt_exist():
    "Tests that elements that shouldn't exist aren't there."
    
    _run_test("tests/resources/installrdf/shouldnt_exist.rdf")

def test_obsolete():
    "Tests that elements that shouldn't exist aren't there."
    
    err = _run_test("tests/resources/installrdf/obsolete.rdf", False)
    assert err.infos

