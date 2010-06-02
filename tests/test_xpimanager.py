import unittest

from xpi import XPIManager

def test_open():
    "Test that the manager will open the package"
    try:
        z = XPIManager("testfiles/install_rdf_only.xpi")
    except:
        assert False
    assert z is not None
    
def test_get_list():
    "Test that the manager can read the file listing"
    z = XPIManager("testfiles/install_rdf_only.xpi")
    assert z.get_file_data()
    
def test_valid_name():
    "Test that the manager can retrieve the correct file name"
    z = XPIManager("testfiles/install_rdf_only.xpi")
    contents = z.get_file_data()
    assert "install.rdf" in contents
    
def test_read_file():
    "Test that a file can be read from the package"
    z = XPIManager("testfiles/install_rdf_only.xpi")
    assert z.read("install.rdf") is not None
