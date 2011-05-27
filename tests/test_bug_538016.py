from js_helper import _do_test


def test_redefinition():
    """Test that global objects can't be redefined."""

    err = _do_test("tests/resources/bug_538016.js")
    # There should be eight errors.
    print err.message_count
    assert err.message_count == 8

