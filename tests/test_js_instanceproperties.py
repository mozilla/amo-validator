from js_helper import _do_test_raw


def test_innerHTML():
    """Tests that the dev can't define event handlers in innerHTML."""

    assert not _do_test_raw("""
    var x = foo();
    x.innerHTML = "<div></div>";
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.innerHTML = "<div onclick=\\"foo\\"></div>";
    """).failed()

    # Test without declaration
    assert _do_test_raw("""
    x.innerHTML = "<div onclick=\\"foo\\"></div>";
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.innerHTML = "x" + y;
    """).failed()


def test_complex_innerHTML():
    """Tests that innerHTML can't be assigned an HTML chunk with bad code"""

    assert not _do_test_raw("""
    var x = foo();
    x.innerHTML = "<script src=\\"chrome://foo.bar/\\"></script>";
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.innerHTML = "<script src=\\"http://foo.bar/\\"></script>";
    """).failed()


def test_on_event():
    """Tests that on* properties are not assigned strings."""

    assert not _do_test_raw("""
    var x = foo();
    x.fooclick = "bar";
    """).failed()

    assert not _do_test_raw("""
    var x = foo();
    x.onclick = function() {};
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.onclick = "bar";
    """).failed()


def test_on_event_null():
    """Null should not trigger on* events."""

    assert not _do_test_raw("""
    var x = foo(),
        y = null;
    x.onclick = y;
    """).failed()

