import validator.testcases.content as test_content
from validator.constants import FIREFOX_GUID
from validator.decorator import version_range
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager


def test_denied_files():
    """
    Tests the validator's ability to hash each individual file and (based on
    this information) determine whether the addon passes or fails the
    validation process.
    """

    package_data = open('tests/resources/denied_libraries/blocked.xpi')
    package = XPIManager(package_data, mode='r', name='blocked.xpi')
    err = ErrorBundle()

    test_content.test_packed_packages(err, package)

    print err.print_summary()

    assert err.notices
    assert not err.failed()
    assert err.metadata.get('identified_files') == {'test.js': {
        'path': 'This file is a false script to facilitate '
                'testing of denied libraries.'}}


def test_skip_denied_file():
    """Ensure denied files are skipped for processing."""

    package_data = open('tests/resources/denied_libraries/errors.xpi')
    package = XPIManager(package_data, mode='r', name='errors.xpi')
    err = ErrorBundle()

    test_content.test_packed_packages(err, package)

    print err.print_summary()
    assert err.notices
    assert not err.failed()


def test_validate_libs_in_compat_mode():
    xpi = 'tests/resources/denied_libraries/addon_with_mootools.xpi'
    with open(xpi) as data:
        package = XPIManager(data, mode='r', name='addon_with_mootools.xpi')
        appversions = {FIREFOX_GUID: version_range('firefox',
                                                   '39.0a1', '39.*')}
        err = ErrorBundle(for_appversions=appversions)
        test_content.test_packed_packages(err, package)
    assert err.get_resource('scripts'), (
                    'expected mootools scripts to be marked for proessing')
    assert err.get_resource('scripts')[0]['scripts'] == set(['content/mootools.js'])
