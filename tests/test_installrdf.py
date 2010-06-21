import testcases.installrdf
from errorbundler import ErrorBundle
from rdf import RDFParser
from helper import _do_test
from constants import *

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
                testcases.installrdf._test_id,
                False)
    _test_value("abc@foo.bar",
                testcases.installrdf._test_id,
                False)
    _test_value("a+bc@foo.bar",
                testcases.installrdf._test_id,
                False)
    
def test_fail_id():
    "Tests that invalid IDs will not be accepted."
    
    _test_value("{1234567-1234-1234-1234-123456789012}",
                testcases.installrdf._test_id)
    _test_value("!@foo.bar",
                testcases.installrdf._test_id)
    
def test_pass_version():
    "Tests that valid versions will be accepted."
    
    _test_value("1.2.3.4",
                testcases.installrdf._test_version,
                False)
    _test_value("1a.2+.3b",
                testcases.installrdf._test_version,
                False)
    
def test_fail_version():
    "Tests that invalid versions will not be accepted."
    
    _test_value("2.0 alpha",
                testcases.installrdf._test_id)
    _test_value("1.2alpha",
                testcases.installrdf._test_id)

def _run_test(filename, failure=True):
    "Runs a test on an install.rdf file"
    
    err = ErrorBundle(None, True)
    
    file_ = open(filename)
    data = file_.read()
    file_.close()
    
    parser = RDFParser(data)
    testcases.installrdf._test_rdf(err, parser)
    
    if failure:
        assert err.failed()
    else:
        assert not err.failed()
    

def test_passing():
    "Tests a passing install.rdf package."
    
    _run_test("tests/resources/installrdf/pass.rdf", False)

