from js_helper import _do_test


def test_double_escaped():
    """Test that escaped characters don't result in errors."""

    err = _do_test("tests/resources/bug_626878.js")
    assert not err.message_count

