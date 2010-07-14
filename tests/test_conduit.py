import os

import validator.decorator as decorator
import validator.testcases as testcases
import validator.testcases.conduit as conduit
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager
from validator.rdf import RDFParser
from helper import _do_test
from validator.constants import *

def test_outright():
    "Tests the Conduit detector against an outright toolbar."
    
    _do_test("tests/resources/conduit/basta_bar.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
    
def test_white():
    "Tests a non-Conduit addon against the library."
    
    _do_test("tests/resources/conduit/pass.xpi",
             conduit.test_conduittoolbar,
             failure=False,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
    
def test_params():
    """Tests the Conduit detector against a toolbar with parameters in
    the install.rdf file that indiciate Conduit-ion."""
    
    _do_test("tests/resources/conduit/conduit_params.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
    
def test_updateurl():
    """Tests the Conduit detector against a toolbar with its updateURL
    parameter set to that of a Conduit Toolbar's."""
    
    _do_test("tests/resources/conduit/conduit_updateurl.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
    
def test_structure():
    """Tests the Conduit detector against a toolbar with files and
    folders which resemble those of a Conduit toolbar."""
    
    _do_test("tests/resources/conduit/conduit_structure.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
    
def test_chrome():
    """Tests the Conduit detector against a toolbar with
    chrome.manifest entries that indicate a Conduit toolbar."""
    
    _do_test("tests/resources/conduit/conduit_chrome.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)
