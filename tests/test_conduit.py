import os

import decorator
import testcases
import testcases.conduit
from errorbundler import ErrorBundle
from xpi import XPIManager
from rdf import RDFParser
from constants import *

def _do_test(path, failure=True):
    
    package_data = open(path)
    package = XPIManager(package_data, path)
    contents = package.get_file_data()
    err = ErrorBundle(None, True)
    
    # Populate in the dependencies.
    err.set_type(PACKAGE_EXTENSION) # Conduit test requires type
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
    
    _do_test("tests/resources/conduit/basta_bar.xpi")
    
def test_white():
    "Tests a non-Conduit addon against the library."
    
    _do_test("tests/resources/conduit/pass.xpi", False)
    
def test_params():
    """Tests the Conduit detector against a toolbar with parameters in
    the install.rdf file that indiciate Conduit-ion."""
    
    _do_test("tests/resources/conduit/conduit_params.xpi")
    
def test_updateurl():
    """Tests the Conduit detector against a toolbar with its updateURL
    parameter set to that of a Conduit Toolbar's."""
    
    _do_test("tests/resources/conduit/conduit_updateurl.xpi")
    
def test_structure():
    """Tests the Conduit detector against a toolbar with files and
    folders which resemble those of a Conduit toolbar."""
    
    _do_test("tests/resources/conduit/conduit_structure.xpi")
    
def test_chrome():
    """Tests the Conduit detector against a toolbar with
    chrome.manifest entries that indicate a Conduit toolbar."""
    
    _do_test("tests/resources/conduit/conduit_structure.xpi")
