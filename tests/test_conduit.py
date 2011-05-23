import validator.decorator as decorator
import validator.testcases as testcases
import validator.testcases.conduit as conduit
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager
from validator.rdf import RDFParser
from helper import _do_test
from validator.constants import *


def test_invalid_package_type():
    """Assert that conduit toolbars can only be extensions."""

    err = ErrorBundle()
    err.detected_type = PACKAGE_ANY
    assert conduit.test_conduittoolbar(err) is None
    err.detected_type = PACKAGE_THEME
    assert conduit.test_conduittoolbar(err) is None
    err.detected_type = PACKAGE_SEARCHPROV
    assert conduit.test_conduittoolbar(err) is None


def test_outright():
    """Test the Conduit detector against an outright toolbar."""

    _do_test("tests/resources/conduit/basta_bar.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)


def test_white():
    """Test a non-Conduit addon against the library."""

    _do_test("tests/resources/conduit/pass.xpi",
             conduit.test_conduittoolbar,
             failure=False,
             require_install=True,
             set_type=PACKAGE_EXTENSION)


def test_params():
    """
    Tests the Conduit detector against a toolbar with parameters in the
    install.rdf file that indiciate Conduit-ion.
    """

    _do_test("tests/resources/conduit/conduit_params.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)


def test_updateurl():
    """
    Test the Conduit detector against a toolbar with its updateURL parameter
    set to that of a Conduit Toolbar's.
    """

    _do_test("tests/resources/conduit/conduit_updateurl.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)


def test_structure():
    """
    Test the Conduit detector against a toolbar with files and folders which
    resemble those of a Conduit toolbar.
    """

    _do_test("tests/resources/conduit/conduit_structure.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)


def test_chrome():
    """
    Test the Conduit detector against a toolbar with chrome.manifest entries
    that indicate a Conduit toolbar.
    """

    _do_test("tests/resources/conduit/conduit_chrome.xpi",
             conduit.test_conduittoolbar,
             failure=True,
             require_install=True,
             set_type=PACKAGE_EXTENSION)

