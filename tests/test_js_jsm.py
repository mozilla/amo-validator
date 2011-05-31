from js_helper import _do_test_raw


def test_jsm_global_overwrites():
    """
    JavaScript modules do not cause global scope conflicts, so we should not
    make errors if globals are overwritten.
    """

    assert _do_test_raw("""
    String.prototype.foo = "bar";
    """).failed()

    assert not _do_test_raw("""
    String.prototype.foo = "bar";
    """, path="test.jsm").failed()


def test_jsm_EXPORTED_SYMBOLS():
    """Test that EXPORTED_SYMBOLS is a trigger for JSM."""

    assert not _do_test_raw("""
    var EXPORTED_SYMBOLS = foo;
    String.prototype.foo = "bar";
    """).failed()

