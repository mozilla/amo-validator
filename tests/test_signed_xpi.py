from nose.tools import eq_

from helper import MockXPI

import validator.testcases.content as content
from validator.errorbundler import ErrorBundle


def test_unsigned_xpi():
    """Test that unsigned packages don't raise warning"""
    x = MockXPI()

    err = ErrorBundle()
    err.supported_versions = {}

    content.test_signed_xpi(err, x)

    assert not err.failed()


def test_mozilla_signed_xpi():
    """Test that signed packages raise warning"""
    x = MockXPI({
        'META-INF/manifest.mf': 'tests/resources/main/foo.bar',
        'META-INF/mozilla.rsa': 'tests/resources/main/foo.bar',
        'META-INF/mozilla.sf': 'tests/resources/main/foo.bar',
    })

    err = ErrorBundle()
    err.supported_versions = {}

    content.test_signed_xpi(err, x)

    assert err.failed()
    assert err.warnings
    assert not err.errors

    eq_(err.warnings[0]['id'], ('testcases_content', 'signed_xpi'))


def test_other_signed_xpi():
    """Test that signed packages raise warning"""
    x = MockXPI({
        'META-INF/manifest.mf': 'tests/resources/main/foo.bar',
        'META-INF/zigbert.rsa': 'tests/resources/main/foo.bar',
        'META-INF/zigbert.sf': 'tests/resources/main/foo.bar',
    })

    err = ErrorBundle()
    err.supported_versions = {}

    content.test_signed_xpi(err, x)

    assert err.failed()
    assert err.warnings
    assert not err.errors

    eq_(err.warnings[0]['id'], ('testcases_content', 'signed_xpi'))


def test_mozilla_signed_multi_xpi():
    """Test that mozilla signed inner packages don't raise an error."""
    xpi = MockXPI({
        'META-INF/manifest.mf': 'tests/resources/main/foo.bar',
        'META-INF/mozilla.rsa': 'tests/resources/main/foo.bar',
        'META-INF/mozilla.sf': 'tests/resources/main/foo.bar',
    }, subpackage=True)

    err = ErrorBundle()
    err.supported_versions = {}
    err.push_state('sub.xpi')
    err.save_resource('is_multipackage', True)

    content.test_signed_xpi(err, xpi)

    assert not err.failed()


def test_unsigned_multi_xpi():
    """Test that unsigned inner packages raise an error."""
    xpi = MockXPI(subpackage=True)

    err = ErrorBundle()
    err.supported_versions = {}
    err.push_state('sub.xpi')
    err.save_resource('is_multipackage', True)

    content.test_signed_xpi(err, xpi)

    assert err.failed()
    assert not err.warnings
    assert err.errors
    eq_(err.errors[0]['id'], ('testcases_content', 'unsigned_sub_xpi'))


def test_other_signed_multi_xpi():
    """Test that other signed inner packages raise an error."""
    xpi = MockXPI({
        'META-INF/manifest.mf': 'tests/resources/main/foo.bar',
        'META-INF/zigbert.rsa': 'tests/resources/main/foo.bar',
        'META-INF/zigbert.sf': 'tests/resources/main/foo.bar',
    }, subpackage=True)

    err = ErrorBundle()
    err.supported_versions = {}
    err.push_state('sub.xpi')
    err.save_resource('is_multipackage', True)

    content.test_signed_xpi(err, xpi)

    assert err.failed()
    assert not err.warnings
    assert err.errors
    eq_(err.errors[0]['id'], ('testcases_content', 'unsigned_sub_xpi'))


def test_unsigned_inner_xpi():
    """Test that inner XPIs need to be signed even if not multi-package."""
    xpi = MockXPI(subpackage=True)

    err = ErrorBundle()
    err.supported_versions = {}
    err.push_state('inner.xpi')
    err.save_resource('is_multipackage', False)

    content.test_signed_xpi(err, xpi)

    assert err.failed()


def test_unsigned_inner_jar():
    """Test that inner packages don't need to be signed if not multipackage."""
    xpi = MockXPI(subpackage=True)
    xpi.filename = 'mock_jar.jar'

    err = ErrorBundle()
    err.supported_versions = {}
    err.push_state('inner.jar')
    err.save_resource('is_multipackage', False)

    content.test_signed_xpi(err, xpi)

    assert not err.failed()
