import os

import decorator
import testcases
import testcases.conduit
from errorbundler import ErrorBundle
from xpi import XPIManager
from rdf import RDFParser

def _do_test(path, failure=True):
    
    package_data = open(path)
    package = XPIManager(package_data, path)
    contents = package.get_file_data()
    err = ErrorBundle(None, True)
    
    # Populate in the dependencies.
    err.set_type(1) # Conduit test requires type
    err.save_resource("has_install_rdf", True)
    rdf_data = package.read("install.rdf")
    install_rdf = RDFParser(rdf_data)
    err.save_resource("install_rdf", install_rdf)
    
    testcases.conduit.test_conduittoolbar(err,
                                          contents,
                                          package)
    
    err.print_summary()
    
    if failure:
        assert err.failed()
    else:
        assert not err.failed()
    
def test_outright():
    "Tests the Conduit detector against an outright toolbar."
    
    _do_test("tests/resources/conduit/fail.xpi")
    
def test_white():
    "Tests a non-Conduit addon against the library."
    
    _do_test("tests/resources/conduit/pass.xpi", False)
    
