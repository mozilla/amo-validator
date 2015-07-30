"""Tests various aspects of the JS traverser."""
import mock

from nose.tools import eq_

from .js_helper import _do_real_test_raw as _test_js


@mock.patch("validator.testcases.javascript.traverser.JSWrapper")
def test_js_traversal_error_reporting(JSWrapper):
    """Test that an internal error in JS traversal is correctly reported as
    a system error."""

    JSWrapper.side_effect = Exception("Inigo Montoya...")
    err = _test_js("hello();", path="my_name_is.js")

    eq_(len(err.errors), 1)
    eq_(err.errors[0]['id'], ("validator", "unexpected_exception"))
    eq_(err.errors[0]['file'], "my_name_is.js")
