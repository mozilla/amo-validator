import hashlib
import json

from js_helper import _do_real_test_raw as _js_test
from validator.testcases.markup.markuptester import MarkupParser
import validator.testcases.jetpack as jetpack
from validator.errorbundler import ErrorBundle
from validator.xpi import XPIManager


def _do_test(xpi_package, allow_old_sdk=True, compat=False):

    err = ErrorBundle()
    if compat:
        err.save_resource('is_compat_test', True)
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
    assert err.metadata.get('is_jetpack', False) is False


def test_package_json_jetpack():
    """Test that add-ons with the new package.json are treated as jetpack."""
    err = _do_test(MockXPI({'bootstrap.js': '', 'package.json': ''}))
    assert not err.errors
    assert not err.warnings
    assert not err.notices
    assert err.metadata.get('is_jetpack') is True


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


def test_mismatched_db_hash():
    """
    Test that failure occurs when the hash of a file doesn't exist in the
    Jetpack known file database.
    """

    with open('tests/resources/bootstrap.js') as bootstrap_file:
        bootstrap = bootstrap_file.read()
        # Break the hash with this.
        bootstrap = 'function() {}; %s' % bootstrap

    err = _do_test(MockXPI({'bootstrap.js': bootstrap,
                            'package.json': '{}'}))
    print err.print_summary(verbose=True)
    assert not err.failed()

    assert 'jetpack_identified_files' in err.metadata

    assert 'jetpack_unknown_files' in err.metadata
    unknown_files = err.metadata['jetpack_unknown_files']
    assert len(unknown_files) == 2
    assert 'bootstrap.js' in unknown_files


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
        assert err.metadata['requires_chrome'] is False
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
        assert err.metadata['requires_chrome'] is True

    for case in interfaces:
        yield interface_cases, case


def test_absolute_uris_in_js():
    """
    Test that a warning is thrown for absolute URIs within JS files.
    """

    bad_js = 'alert("resource://foo-data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err = _js_test(bad_js, jetpack=True)
    assert err.failed()
    assert err.compat_summary['errors']

    # Test that literals are inspected even if they're the result of an
    # operation.
    bad_js = 'alert("resou" + "rce://foo-" + "data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err = _js_test(bad_js, jetpack=True)
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


def test_fail_on_cfx():
    """
    Test that we fail for add-ons built with 'cfx'.
    """

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
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed() and err.errors


def test_pass_cfx_for_compat():
    """
    Test that we fail for add-ons built with 'cfx'.
    """

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
                                json.dumps(harnessoptions)}),
                   compat=True)
    print err.print_summary(verbose=True)
    assert not err.failed() and not err.errors
