from zipfile import ZipFile
from validator.xpi import XPIManager


def test_open():
    "Test that the manager will open the package"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert z is not None


def test_get_list():
    "Test that the manager can read the file listing"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert z.get_file_data()


def test_valid_name():
    "Test that the manager can retrieve the correct file name"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    contents = z.get_file_data()
    assert "install.rdf" in contents
    assert z.test() == False


def test_read_file():
    "Test that a file can be read from the package"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert z.read("install.rdf") is not None


def test_bad_file():
    "Tests that the XPI manager correctly reports a bad XPI file."

    x = XPIManager("tests/resources/junk.xpi")
    assert not x.zf

    x = XPIManager("tests/resources/corrupt.xpi")
    assert x.test()


def test_missing_file():
    "Tests that the XPI manager correctly reports a missing XPI file."

    x = XPIManager("tests/resources/foo.bar")
    assert not x.zf

