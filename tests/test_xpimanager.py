import zipfile
from zipfile import ZipFile

from nose.tools import eq_

from validator.xpi import XPIManager


def test_open():
    "Test that the manager will open the package"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert z is not None


def test_get_list():
    "Test that the manager can read the file listing"

    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert not z.contents_cache
    assert z.package_contents()
    assert z.contents_cache  # Spelling check!
    z.contents_cache = "foo"
    eq_(z.package_contents(), "foo")


def test_valid_name():
    "Test that the manager can retrieve the correct file name"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    contents = z.package_contents()
    assert "install.rdf" in contents
    assert z.test() == False


def test_read_file():
    "Test that a file can be read from the package"
    z = XPIManager("tests/resources/xpi/install_rdf_only.xpi")
    assert z.read("install.rdf") is not None


def test_bad_file():
    "Tests that the XPI manager correctly reports a bad XPI file."

    try:
        x = XPIManager("tests/resources/junk.xpi")
    except zipfile.BadZipfile:
        pass

    x = XPIManager("tests/resources/corrupt.xpi")
    assert x.test()


def test_missing_file():
    "Tests that the XPI manager correctly reports a missing XPI file."

    passed = False
    try:
        x = XPIManager("tests/resources/foo.bar")
    except:
        passed = True

    assert passed

