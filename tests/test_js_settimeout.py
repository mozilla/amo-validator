from js_helper import _do_test_raw

def test_settimeout_fail():
    "Test cases in which setTimeout should fail"

    assert _do_test_raw("""
    setTimeout("abc.def()", 1000);
    """).failed()

    assert _do_test_raw("""
    window["set" + "Timeout"]("abc.def()", 1000);
    """).failed()

    assert _do_test_raw("""
    var x = "foo.bar()";
    setTimeout(x, 1000);
    """).failed()

    assert _do_test_raw("""
    var x = "foo.bar()";
    window["set" + "Timeout"](x, 1000);
    """).failed()


def test_settimeout_pass():
    "Test cases in which setTimeout should be allowed"

    assert not _do_test_raw("""
    setTimeout(function(){foo.bar();}, 1000);
    """).failed()

    assert not _do_test_raw("""
    window["set" + "Timeout"](function(){foo.bar();}, 1000);
    """).failed()

    assert not _do_test_raw("""
    setTimeout();
    """).failed()

    assert not _do_test_raw("""
    window["set" + "Timeout"]();
    """).failed()

