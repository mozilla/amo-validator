from js_helper import _do_test_raw

def test_createElement():
    """Tests that createElement calls are filtered properly"""

    assert not _do_test_raw("""
    var x = "foo";
    x.createElement();
    x.createElement("foo");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElement("script");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElement(bar);
    """).failed()


def test_createElementNS():
    """Tests that createElementNS calls are filtered properly"""

    assert not _do_test_raw("""
    var x = "foo";
    x.createElementNS();
    x.createElementNS("foo");
    x.createElementNS("foo", "bar");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElementNS("foo", "script");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElementNS("foo", bar);
    """).failed()


def test_setAttribute():
    """Tests that setAttribute calls are blocked successfully"""

    assert not _do_test_raw("""
    var x = "foo";
    x.setAttribute();
    x.setAttribute("foo");
    x.setAttribute("foo", "bar");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.setAttribute("onfoo", "bar");
    """).failed()
