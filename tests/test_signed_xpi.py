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


def test_signed_xpi():
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

    eq_(err.warnings[0]["id"], ("testcases_content", "signed_xpi"))
