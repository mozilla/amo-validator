from nose.tools import eq_

from js_helper import _do_test_raw

from validator.testcases.javascript.jstypes import JSWrapper
from validator.testcases.javascript.actions import _get_as_num


def test_array_destructuring():
    """
    Make sure that multi-level and prototype array destructuring don't cause
    tracebacks.
    """
    assert not _do_test_raw("""
    [a, b, c, d] = [1, 2, 3, 4];
    [] = bar();
    """).failed()

    assert not _do_test_raw("""
    function foo(x, y, [a, b, c], z) {
        bar();
    }
    """).failed()


def test_get_as_num():
    """Test that _get_as_num performs as expected."""

    def test(input, output):
        eq_(_get_as_num(input), output)

    yield test, 1, 1
    yield test, 1.0, 1.0
    yield test, "1", 1
    yield test, "1.0", 1.0
    yield test, None, 0
    yield test, "0xF", 15
    yield test, True, 1
    yield test, False, 0

    yield test, JSWrapper(3), 3
    yield test, JSWrapper(None), 0


def test_spidermonkey_warning():
    """
    Test that stderr warnings in Spidermonkey do not trip runtime errors.
    """
    # The following is attempting to store the octal "999999999999" in x, but
    # this is an invalid octal obviously. We need to "use strict" here because
    # the latest versions of spidermonkey simply accept that as a base 10
    # number, despite the "0" prefix.
    # We need spidermonkey to choke on this code, and this test makes sure that
    # when spidermonkey does, it doesn't break the validator.
    assert _do_test_raw("""
    "use strict";
    var x = 0999999999999;
    """).failed()
