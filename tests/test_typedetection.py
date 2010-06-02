import os

from errorbundler import ErrorBundle
from rdf import RDFParser
from xpi import XPIManager
import typedetection

def _test_type(file_, expectation):
    "Tests a file against the expectations"
    
    err = ErrorBundle(None, True)
    package = XPIManager(open(file_), file_)
    contents = package.get_file_data()
    
    # We need to have an install.rdf.
    assert "install.rdf" in contents
    
    # Load up the install.rdf into an RDFParser
    install_file = package.read("install.rdf")
    install_rdf = RDFParser(install_file)
    
    results = typedetection.detect_type(err, install_rdf, package)
    
    assert results == expectation
    assert not err.failed()
    
def test_extension():
    "Tests that type detection can detect an addon of type 'extension'"
    
    _test_type("tests/resources/typedetection/extension.xpi", 1)

def test_theme():
    "Tests that type detection can detect an addon of type 'theme'"
    
    _test_type("tests/resources/typedetection/theme.jar", 2)

def test_dictionary():
    "Tests that type detection can detect an addon of type 'dictionary'"
    
    _test_type("tests/resources/typedetection/dictionary.xpi", 3)

def test_langpack():
    "Tests that type detection can detect an addon of type 'langpack'"
    
    _test_type("tests/resources/typedetection/langpack.xpi", 4)
