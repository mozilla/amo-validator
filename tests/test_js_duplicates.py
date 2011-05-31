from js_helper import _do_test_raw


def test_no_dups():
    """Test that errors are not duplicated."""

    assert _do_test_raw("""
    eval("test");
    """).message_count == 1

    assert _do_test_raw("""
    var x = eval();
    """).message_count == 1

    assert _do_test_raw("""
    eval = 123;
    """).message_count == 1

    assert _do_test_raw("""
    eval.prototype = true;
    """).message_count == 2

