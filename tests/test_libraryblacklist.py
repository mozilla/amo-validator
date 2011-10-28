from nose.tools import eq_

import validator.testcases.content as test_content
from validator.compat import FX9_DEFINITION
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager
from validator.rdf import RDFParser


def test_blacklisted_files():
    """
    Tests the validator's ability to hash each individual file and (based on
    this information) determine whether the addon passes or fails the
    validation process.
    """

    package_data = open("tests/resources/libraryblacklist/blocked.xpi")
    package = XPIManager(package_data, mode="r", name="blocked.xpi")
    err = ErrorBundle()

    test_content.test_packed_packages(err, package)

    print err.print_summary()

    assert err.notices
    assert not err.failed()


def test_skip_blacklisted_file():
    """Ensure blacklisted files are skipped for processing."""

    package_data = open("tests/resources/libraryblacklist/errors.xpi")
    package = XPIManager(package_data, mode="r", name="errors.xpi")
    err = ErrorBundle()

    test_content.test_packed_packages(err, package)

    print err.print_summary()
    assert err.notices
    assert not err.failed()


def test_validate_libs_in_compat_mode():
    xpi = "tests/resources/libraryblacklist/addon_with_mootools.xpi"
    with open(xpi) as data:
        package = XPIManager(data, mode="r", name="addon_with_mootools.xpi")
        err = ErrorBundle(for_appversions=FX9_DEFINITION)
        test_content.test_packed_packages(err, package)
    assert err.get_resource("scripts"), (
                    "expected mootools scripts to be marked for proessing")
    eq_(err.get_resource("scripts")[0]["scripts"],
        set(["content/mootools.js"]))
