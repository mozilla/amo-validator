import validator.testcases.content as test_content
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

