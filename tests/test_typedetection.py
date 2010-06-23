import os

from errorbundler import ErrorBundle
from rdf import RDFParser
from xpi import XPIManager
from constants import *
import typedetection

def _test_type(file_, expectation, failure=False):
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
    if not failure:
        assert not err.failed()
    else:
        assert err.failed()

def test_extension():
    """When no install.rdf file is present and the file ends with XPI,
    then the type detection module should return type "Dictionary"."""
    
    _test_type("tests/resources/typedetection/td_bad_dict.xpi", 3)
    
def test_extension():
    "Tests that type detection can detect an addon of type 'extension'"
    
    _test_type("tests/resources/typedetection/td_notype_ext.xpi", 1)

def test_theme():
    "Tests that type detection can detect an addon of type 'theme'"
    
    _test_type("tests/resources/typedetection/td_notype_theme.jar", 2)

def test_dictionary():
    "Tests that type detection can detect an addon of type 'dictionary'"
    
    _test_type("tests/resources/typedetection/td_dictionary.xpi", 3)

def test_langpack():
    """Tests that the type detection module can detect a language pack.
    As an added bonus, this test also verifies that the <em:type>
    element is correctly interpreted."""
    
    _test_type("tests/resources/typedetection/td_langpack.xpi", 4)

def test_bad_emtype():
    """Tests for a bad <em:type> value."""
    
    _test_type("tests/resources/typedetection/td_bad_emtype.xpi",
               None,
               True)

def test_strange():
    """Tests that in install.rdf-less package is listed as being a
    dictionary type if it has an XPI extension and otherwise passes
    back a None object."""
    
    err = ErrorBundle(None, True)
    
    non_langpack = MockXPILangpack()
    langpack = MockXPILangpack(True)
    
    assert typedetection.detect_type(err, None, langpack
                                     ) == PACKAGE_DICTIONARY
    assert typedetection.detect_type(err, None, non_langpack) is None
    

class MockXPILangpack:
    "Simulates a language pack XPI manager object"
    
    def __init__(self, is_xpi=False):
        if is_xpi:
            self.extension = "xpi"
        else:
            self.extension = "foo" # Or anything else
