from js_helper import _do_test, _do_test_raw, _get_var

def test_basic_math():
    "Tests that contexts work and that basic math is executed properly"

    err = _do_test_raw("""
    var x = 1;
    var y = 2;
    var z = x + y;

    var dbz = 1 / 0; // Should return 0, not break the world.
    var dbz1 = 1 % 0;
    var dbz2 = 1;
    var dbz3 = 1;
    dbz2 /= 0;
    dbz3 %= 0;

    var a = 2 + 3;
    var b = a - 1;
    var c = b * 2;
    """)
    assert err.message_count == 0

    assert _get_var(err, "x") == 1
    assert _get_var(err, "y") == 2
    assert _get_var(err, "z") == 3

    assert _get_var(err, "dbz") is None
    assert _get_var(err, "dbz1") is None
    assert _get_var(err, "dbz2") is None
    assert _get_var(err, "dbz3") is None

    assert _get_var(err, "a") == 5
    assert _get_var(err, "b") == 4
    assert _get_var(err, "c") == 8

def test_in_operator():
    "Tests the 'in' operator."

    err = _do_test_raw("""
    var list = ["a",1,2,3,"foo"];
    var dict = {"abc":123, "foo":"bar"};

    // Must be true
    var x = "a" in list;
    var y = "abc" in dict;

    // Must be false
    var a = "bar" in list;
    var b = "asdf" in dict;
    """)
    assert err.message_count == 0
    print err.final_context.output()

    print _get_var(err, "x"), "<<<"
    assert _get_var(err, "x") == True
    assert _get_var(err, "y") == True
    assert _get_var(err, "a") == False
    assert _get_var(err, "b") == False


