# -*- coding: utf8 -*-
import os
import tempfile
from zipfile import BadZipfile, ZipFile

from nose.tools import eq_

from validator.xpi import XPIManager

RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resources')


def get_path(fn):
    return os.path.join(RESOURCES_PATH, fn)


def test_open():
    """Test that the manager will open the package."""
    z = XPIManager(get_path('xpi/install_rdf_only.xpi'))
    assert z is not None


def test_get_list():
    """Test that the manager can read the file listing."""
    z = XPIManager(get_path('xpi/install_rdf_only.xpi'))
    assert not z.contents_cache
    assert z.package_contents()
    assert z.contents_cache  # Spelling check!
    z.contents_cache = 'foo'
    eq_(z.package_contents(), 'foo')


def test_valid_name():
    "Test that the manager can retrieve the correct file name."
    z = XPIManager(get_path('xpi/install_rdf_only.xpi'))
    contents = z.package_contents()
    assert 'install.rdf' in contents
    assert z.test() == False


def test_read_file():
    """Test that a file can be read from the package."""
    z = XPIManager(get_path('xpi/install_rdf_only.xpi'))
    assert z.read('install.rdf') is not None


def test_write_file():
    """Test that a file can be written in UTF-8 to the package."""
    with tempfile.NamedTemporaryFile(delete=False) as t:
        temp_fn = t.name
        try:
            z = XPIManager(temp_fn, mode='w')
            f, d = 'install.rdf', '注目のコレクション'.decode('utf-8')
            z.write(f, d)
            eq_(z.read(f), d.encode('utf-8'))
        finally:
            os.unlink(temp_fn)


def test_bad_file():
    """Tests that the XPI manager correctly reports a bad XPI file."""
    try:
        x = XPIManager(get_path('junk.xpi'))
    except BadZipfile:
        pass
    x = XPIManager(get_path('corrupt.xpi'))
    assert x.test()


def test_missing_file():
    """Tests that the XPI manager correctly reports a missing XPI file."""
    passed = False
    try:
        x = XPIManager('foo.bar')
    except:
        passed = True
    assert passed
