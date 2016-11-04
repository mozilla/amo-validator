from itertools import repeat

from .helper import _do_test, MockXPI

from validator.errorbundler import ErrorBundle
from validator.testcases import packagelayout


def test_denied_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""

    err = _do_test('tests/resources/packagelayout/ext_deny.xpi',
                   packagelayout.test_denied_files,
                   True)
    assert err.metadata['contains_binary_extension']
    assert any(warning['id'][1] == 'test_denied_files'
        and warning['file'] == 'omgitsadll.dll' for warning in err.warnings)
    assert not any(count for (key, count) in err.compat_summary.items())

    # Run the compatibility test on this, but it shouldn't fail or produce
    # errors because the bianry content isn't in the appropriate directories.
    err = _do_test('tests/resources/packagelayout/ext_deny.xpi',
                   packagelayout.test_compatibility_binary,
                   False)
    print err.compat_summary
    assert not err.compat_summary['errors']


def test_java_jar_detection():
    """
    Test that Java archives are flagged as such so that they do not generate
    hundreds or thousands of errors.
    """

    classes = ('c%d.class' % i for i in xrange(1000))
    mock_xpi = MockXPI(dict(zip(classes, repeat(''))))
    err = ErrorBundle(None, True)
    packagelayout.test_denied_files(err, mock_xpi)

    assert err.warnings
    assert err.warnings[0]['id'] == ('testcases_packagelayout',
                                     'test_denied_files', 'java_jar')


def test_denied_magic_numbers():
    'Tests that denied magic numbers are banned'

    err = _do_test('tests/resources/packagelayout/magic_number.xpi',
                   packagelayout.test_denied_files,
                   True)
    assert err.metadata['contains_binary_content']

    # Same logic as above.
    err = _do_test('tests/resources/packagelayout/magic_number.xpi',
                   packagelayout.test_compatibility_binary,
                   False)
    print err.compat_summary
    assert not err.compat_summary['errors']
    assert 'binary_components' not in err.metadata


def test_compat_binary_extensions():
    """
    Test that the validator will throw compatibility errors for files that
    would otherwise require the add-on to be manually updated.
    """

    # This time when the compatibility checks are run, they should fire off
    # compatibility errors because the files are the /components/ directory
    # of the package.
    err = _do_test('tests/resources/packagelayout/ext_deny_compat.xpi',
                   packagelayout.test_compatibility_binary,
                   False)
    print err.compat_summary
    assert err.compat_summary['errors']
    assert err.metadata['binary_components']


def test_godlikea():
    """Test that packages with a godlikea chrome namespaceget rejected."""

    err = ErrorBundle()
    xpi = MockXPI({'chrome/godlikea.jar': True})
    packagelayout.test_godlikea(err, xpi)
    assert err.failed()
    assert err.errors


# These functions will test the code with manually constructed packages
# that contain valid or failing versions of the specified package. The
# remaining tests will simply emulate this behaviour (since it was
# successfully tested with these functions).
def test_theme_passing():
    'Tests the layout of a proper theme'

    _do_test('tests/resources/packagelayout/theme.jar',
             packagelayout.test_theme_layout,
             False)


def test_extra_unimportant():
    """Tests the layout of a theme that contains an unimportant but
    extra directory."""

    _do_test('tests/resources/packagelayout/theme_extra_unimportant.jar',
             packagelayout.test_theme_layout,
             False)


def _do_simulated_test(function, structure, failure=False, ff4=False):
    """"Performs a test on a function or set of functions without
    generating a full package."""

    dict_structure = {'__MACOSX/foo.bar': True}
    for item in structure:
        dict_structure[item] = True

    err = ErrorBundle()
    err.save_resource('ff4', ff4)
    function(err, structure)

    err.print_summary(True)

    if failure:
        assert err.failed()
    else:
        assert not err.failed()

    return err


def test_langpack_max():
    """Tests the package layout module out on a simulated language pack
    containing the largest number of possible elements."""

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ['install.rdf',
                        'chrome/foo.jar',
                        'chrome.manifest',
                        'chrome/bar.test.jar',
                        'foo.manifest',
                        'bar.rdf',
                        'abc.dtd',
                        'def.jar',
                        'chrome/asdf.properties',
                        'chrome/asdf.xhtml',
                        'chrome/asdf.css'])


def test_langpack_sans_jars():
    """
    Test that language packs don't require JAR files to be present in the
    chrome/ directory.
    """

    _do_simulated_test(
            packagelayout.test_langpack_layout,
            ['install.rdf', 'chrome.manifest',  # Required files
             'foo.manifest', 'bar.rdf', 'abc.dtd', 'def.jar',  # Allowed files
             'chrome/foo.properties', 'chrome/foo.xhtml', 'chrome/foo.css'])


def test_dict_max():
    """Tests the package layout module out on a simulated dictionary
    containing the largest number of possible elements."""

    _do_simulated_test(packagelayout.test_dictionary_layout,
                       ['install.rdf',
                        'dictionaries/foo.aff',
                        'dictionaries/bar.test.dic',
                        'install.js',
                        'dictionaries/foo.aff',
                        'dictionaries/bar.test.dic',
                        'chrome.manifest',
                        'chrome/whatever.jar'])


def test_unknown_file():
    """Tests that the unknown file detection function is working."""

    # We test against langpack because it is incredibly strict in its
    # file format.

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ['install.rdf',
                        'chrome/foo.jar',
                        'chrome.manifest',
                        'chromelist.txt'])


def test_disallowed_file():
    """Tests that outright improper files are blocked."""

    # We test against langpack because it is incredibly strict in its
    # file format.

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ['install.rdf',
                        'chrome/foo.jar',
                        'chrome.manifest',
                        'foo.bar'],
                       True)


def test_extra_obsolete():
    """Tests that unnecessary, obsolete files are detected."""

    err = ErrorBundle()

    # Tests that chromelist.txt is treated (with and without slashes in
    # the path) as an obsolete file.
    assert not packagelayout.test_unknown_file(err, 'x//whatever.txt')
    assert not packagelayout.test_unknown_file(err, 'whatever.txt')
    assert packagelayout.test_unknown_file(err, 'x//chromelist.txt')
    assert packagelayout.test_unknown_file(err, 'chromelist.txt')

    assert not err.failed()


def test_has_installrdfs():
    """Tests that install.rdf files are present and that subpackage
    rules are respected."""

    # Test package to make sure has_install_rdf is set to True.
    assert not _do_config_test(packagelayout.test_layout_all)
    assert _do_config_test(
        packagelayout.test_layout_all, has_install_rdf=False)

    mock_xpi_subpack = MockXPI({}, subpackage=True)

    # Makes sure the above test is ignored if the package is a
    # subpackage.
    assert not _do_config_test(packagelayout.test_layout_all,
                               has_install_rdf=False,
                               xpi=mock_xpi_subpack)
    assert not _do_config_test(packagelayout.test_layout_all,
                               has_install_rdf=True,
                               xpi=mock_xpi_subpack)


def test_has_package_json():
    """Tests that having an install.rdf is not required with a package.json."""
    assert not _do_config_test(
        packagelayout.test_layout_all,
        has_install_rdf=False,
        has_package_json=True), 'errors when only package.json present'


def test_no_package_json():
    """Tests that there are errors when there is not an install.rdf or a
    package.json"""
    assert _do_config_test(
        packagelayout.test_layout_all,
        has_install_rdf=False,
        has_package_json=False), (
        'no errors and no install.rdf or package.json')


def test_has_manifest_json():
    """Tests that having an install.rdf or package.json is not required with a
    manifest.json."""
    assert not _do_config_test(
        packagelayout.test_layout_all,
        has_install_rdf=False,
        has_package_json=False,
        has_manifest_json=True), 'errors when only manifest.json present'


def test_no_manifest_json():
    """Tests that there are errors when there is not an install.rdf or a
    package.json or a manifest.json"""
    assert _do_config_test(
        packagelayout.test_layout_all,
        has_install_rdf=False,
        has_package_json=False,
        has_manifest_json=False), (
        'no errors and no install.rdf or package.json or manifest.json')


class MockDupeZipFile(object):
    """Mock a ZipFile class, simulating duplicate filename entries."""

    def namelist(self):
        return ['foo.bar', 'foo.bar']


class MockDupeXPI(object):
    """Mock the XPIManager class, simulating duplicate filename entries."""

    def __init__(self):
        self.zf = MockDupeZipFile()
        self.subpackage = False


def test_duplicate_files():
    """Test that duplicate files in a package are caught."""

    err = ErrorBundle()
    err.save_resource('has_install_rdf', True)
    packagelayout.test_layout_all(err, MockDupeXPI())
    assert err.failed()


def _do_config_test(function, has_install_rdf=True, has_package_json=False,
                    has_manifest_json=False, xpi=None):
    'Helps to test that install.rdf files are present'

    err = ErrorBundle()

    content = {}
    if has_install_rdf:
        content['install.rdf'] = True
        err.save_resource('has_install_rdf', True)
    if has_package_json:
        content['package.json'] = True
        err.save_resource('has_package_json', True)
    if has_manifest_json:
        content['manifest.json'] = True
        err.save_resource('has_manifest_json', True)

    if xpi is None:
        xpi = MockXPI(content)
    function(err, xpi)

    return err.failed()
