from nose.tools import eq_

import hashlib
import json
import nose

from js_helper import _do_real_test_raw as _js_test
from validator.testcases.markup.markuptester import MarkupParser
import validator.testcases.jetpack as jetpack
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager


def _do_test(xpi_package, allow_old_sdk=True):

    err = ErrorBundle()
    jetpack.inspect_jetpack(err, xpi_package, allow_old_sdk=allow_old_sdk)
    return err


class MockXPI(object):

    def __init__(self, resources):
        self.resources = resources

    def read(self, name):
        if isinstance(self.resources[name], bool):
            return ''
        return self.resources[name]

    def __iter__(self):
        for name in self.resources.keys():
            yield name

    def __contains__(self, name):
        return name in self.resources


def test_not_jetpack():
    """Test that add-ons which do not match the Jetpack pattern are ignored."""

    err = _do_test(MockXPI({'foo': True, 'bar': True}))
    assert not err.errors
    assert not err.warnings
    assert not err.notices
    eq_(err.metadata.get('is_jetpack', False), False)


def test_package_json_jetpack():
    """Test that add-ons with the new package.json are treated as jetpack."""
    err = _do_test(MockXPI({'bootstrap.js': '', 'package.json': ''}))
    assert not err.errors
    assert not err.warnings
    assert not err.notices
    eq_(err.metadata.get('is_jetpack'), True)


def test_bad_harnessoptions():
    """Test that a malformed harness-options.json file is warned against."""

    err = _do_test(MockXPI({'bootstrap.js': True,
                            'components/harness.js': True,
                            'harness-options.json': 'foo bar'}))
    assert err.failed()
    assert err.warnings
    print err.warnings
    assert err.warnings[0]['id'][-1] == 'bad_harness-options.json'


def test_pass_jetpack():
    """Test that a minimalistic Jetpack setup will pass."""

    harnessoptions = {'sdkVersion': '1.17',
                      'jetpackID': '',
                      'manifest': {}}

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert 'is_jetpack' in err.metadata and err.metadata['is_jetpack']

    # Test that all files are marked as pretested.
    pretested_files = err.get_resource('pretested_files')
    assert pretested_files
    assert 'bootstrap.js' in pretested_files


def test_package_json_pass_jetpack():
    """Test that a minimalistic package.json Jetpack setup will pass."""

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'package.json': '{}'}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert 'is_jetpack' in err.metadata and err.metadata['is_jetpack']

    # Test that all files are marked as pretested.
    pretested_files = err.get_resource('pretested_files')
    assert pretested_files
    assert 'bootstrap.js' in pretested_files


def test_package_json_different_bootstrap():
    """Test that a minimalistic package.json Jetpack setup will pass."""

    err = _do_test(MockXPI({'bootstrap.js': "var foo = 'bar';",
                            'package.json': '{}'}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert 'is_jetpack' in err.metadata and err.metadata['is_jetpack']

    # Test that all files are not marked as pretested.
    pretested_files = err.get_resource('pretested_files')
    assert not pretested_files
    assert 'bootstrap.js' not in pretested_files


def test_missing_elements():
    """Test that missing elements in harness-options will fail."""

    harnessoptions = {'sdkVersion': '1.17',
                      'jetpackID': ''}

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    assert err.failed()


def test_skip_safe_files():
    """Test that missing elements in harness-options will fail."""

    harnessoptions = {'sdkVersion': '1.17',
                      'jetpackID': '',
                      'manifest': {}}

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions),
                            'foo.png': True,
                            'bar.JpG': True,
                            'safe.GIF': True,
                            'icon.ico': True,
                            'foo/.DS_Store': True}))
    assert not err.failed()


def test_pass_manifest_elements():
    """Test that proper elements in harness-options will pass."""

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            'jetpackID': 'foobar',
            'sdkVersion': '1.17',
            'manifest': {
                'bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'sectionName': 'lib',
                     'moduleName': 'drawing',
                     'jsSHA256': bootstrap_hash,
                     'docsSHA256': bootstrap_hash}}}

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions),
                            'resources/bootstrap.js': bootstrap}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert 'jetpack_loaded_modules' in err.metadata
    nose.tools.eq_(err.metadata['jetpack_loaded_modules'],
                   ['addon-kit-lib/drawing.js'])
    assert 'jetpack_identified_files' in err.metadata
    assert 'identified_files' in err.metadata
    assert 'bootstrap.js' in err.metadata['jetpack_identified_files']
    assert 'bootstrap.js' in err.metadata['identified_files']

    assert 'jetpack_unknown_files' in err.metadata
    assert not err.metadata['jetpack_unknown_files']


def test_ok_resource():
    """Test that resource:// URIs aren't flagged."""

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            'jetpackID': 'foobar',
            'sdkVersion': '1.17',
            'manifest': {
                'resource://bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'sectionName': 'lib',
                     'moduleName': 'drawing',
                     'jsSHA256': bootstrap_hash,
                     'docsSHA256': bootstrap_hash}}}

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'resources/bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()


def test_bad_resource():
    """Test for failure on non-resource:// modules."""

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            'sdkVersion': '1.17',
            'jetpackID': 'foobar',
            'manifest':
                {'http://foo.com/bar/bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'sectionName': 'lib',
                     'moduleName': 'drawing',
                     'jsSHA256': bootstrap_hash,
                     'docsSHA256': bootstrap_hash}}}

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'resources/bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_missing_manifest_elements():
    """Test that missing manifest elements in harness-options will fail."""

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            'sdkVersion': '1.17',
            'jetpackID': 'foobar',
            'manifest':
                {'resource://bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'moduleName': 'drawing',
                     'jsSHA256': bootstrap_hash,
                     'docsSHA256': bootstrap_hash}}}

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'resources/bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_mismatched_hash():
    """
    Test that failure occurs when the actual file hash doesn't match the hash
    provided by harness-options.js.
    """

    harnessoptions = {
            'sdkVersion': '1.17',
            'jetpackID': 'foobar',
            'manifest':
                {'resource://bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'moduleName': 'drawing',
                     'jsSHA256': '',
                     'docsSHA256': ''}}}

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'resources/bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_mismatched_db_hash():
    """
    Test that failure occurs when the hash of a file doesn't exist in the
    Jetpack known file database.
    """

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        # Break the hash with this.
        bootstrap = 'function() {}; %s' % bootstrap
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            'sdkVersion': '1.17',
            'jetpackID': 'foobar',
            'manifest':
                {'resource://bootstrap.js':
                    {'requirements': {},
                     'packageName': 'addon-kit',
                     'moduleName': 'drawing',
                     'sectionName': 'lib',
                     'jsSHA256': bootstrap_hash,
                     'docsSHA256': bootstrap_hash}}}

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'resources/bootstrap.js': bootstrap,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()

    assert 'jetpack_loaded_modules' in err.metadata
    assert not err.metadata['jetpack_loaded_modules']
    assert 'jetpack_identified_files' in err.metadata

    assert 'jetpack_unknown_files' in err.metadata
    unknown_files = err.metadata['jetpack_unknown_files']
    nose.tools.eq_(len(unknown_files), 2)
    nose.tools.ok_('bootstrap.js' in unknown_files)
    nose.tools.ok_('resources/bootstrap.js' in unknown_files)


def test_mismatched_module_version():
    """
    Tests that add-ons using modules from a version of the SDK
    other than the version they claim.
    """

    xpi = XPIManager('tests/resources/jetpack/jetpack-1.8-pretending-1.8.1.xpi')
    err = _do_test(xpi)

    assert err.failed()
    assert any(w['id'][2] == 'mismatched_version' for w in err.warnings)


def test_new_module_location_spec():
    """
    Tests that we don't fail for missing modules in add-ons generated with
    newer versions of the SDK.
    """

    xpi = XPIManager('tests/resources/jetpack/jetpack-1.14.xpi')
    err = _do_test(xpi)

    assert not any(w['id'][2] == 'missing_jetpack_module'
                   for w in err.warnings)


def test_components_flagged():
    """Test that `Components` is flagged in Jetpack."""

    js = """
    var x = Components.services.foo.bar;
    """
    assert not _js_test(js).failed()
    assert _js_test(js, jetpack=True).failed()


def test_safe_require():
    """Test that requiring an innocuous module does not add the
    requires_chrome flag."""

    def base_case():
        err = _js_test("""var foo = require("bar");""",
                       jetpack=True)
        eq_(err.metadata['requires_chrome'], False)
    yield base_case


def test_unsafe_safe_require():
    """Test that requiring low-level modules does add the requires_chrome
    flag."""

    interfaces = ['chrome', 'window-utils', 'observer-service']

    def interface_cases(interface):
        err = _js_test("""var {cc, ci} = require("%s")""" % interface,
                       jetpack=True)
        print err.print_summary(verbose=True)

        first_message = err.warnings[0]['message']
        assert 'non-SDK interface' in first_message, ('unexpected: %s' %
                                                          first_message)
        assert 'requires_chrome' in err.metadata, \
                'unexpected: "requires_chrome" should be in metadata'
        eq_(err.metadata['requires_chrome'], True)

    for case in interfaces:
        yield interface_cases, case


def test_absolute_uris_in_js():
    """
    Test that a warning is thrown for absolute URIs within JS files.
    """

    bad_js = 'alert("resource://foo-data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err =_js_test(bad_js, jetpack=True)
    assert err.failed()
    assert err.compat_summary['errors']

    # Test that literals are inspected even if they're the result of an
    # operation.
    bad_js = 'alert("resou" + "rce://foo-" + "data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err =_js_test(bad_js, jetpack=True)
    assert err.failed()
    assert err.compat_summary['errors']


def test_observer_service_flagged():
    assert _js_test("""
    var {Ci} = require("chrome");
    thing.QueryInterface(Ci.nsIObserverService);
    """, jetpack=True).failed()

    assert not _js_test("""
    thing.QueryInterface(Ci.nsIObserverService);
    """).failed()


def test_absolute_uris_in_markup():
    """
    Test that a warning is thrown for absolute URIs within markup files.
    """

    err = ErrorBundle()
    bad_html = '<foo><bar src="resource://foo-data/bar/zap.png" /></foo>'

    parser = MarkupParser(err)
    parser.process('foo.html', bad_html, 'html')
    assert not err.failed()

    err.metadata['is_jetpack'] = True
    parser = MarkupParser(err)
    parser.process('foo.html', bad_html, 'html')
    assert err.failed()
    assert err.compat_summary['errors']


def test_bad_sdkversion():
    """Test that a redacted SDK version is not used."""

    harnessoptions = {'sdkVersion': '1.4',
                      'jetpackID': '',
                      'manifest': {}}

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
    with open('jetpack/addon-sdk/lib/sdk/test/harness.js') as harness_file:
        harness = harness_file.read()
    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'components/harness.js': harness,
                            'harness-options.json':
                                json.dumps(harnessoptions)}))
    assert err.failed() and err.errors


def test_outdated_sdkversion():
    """
    Tests that add-ons using a version other than the latest release
    are warned against, but module hashes are still recognized.
    """

    xpi = XPIManager('tests/resources/jetpack/jetpack-1.8-outdated.xpi')
    err = _do_test(xpi, allow_old_sdk=False)

    assert err.failed()
    # Make sure we don't have any version mismatch warnings
    eq_(len(err.warnings), 1)
    eq_(err.warnings[0]['id'][2], 'outdated_version')


def test_future_sdkversion():
    """
    Test that if the developer is using a verison of the SDK that's newer than
    the latest recognized version, we don't throw an error.
    """

    xpi = XPIManager('tests/resources/jetpack/jetpack-1.8-future.xpi')
    err = _do_test(xpi, allow_old_sdk=False)

    print err.print_summary(verbose=True)
    assert not err.failed()

