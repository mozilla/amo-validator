from js_helper import _do_test, _do_test_raw, _get_var

def test_basic_math():
    "Tests that contexts work and that basic math is executed properly"

    err = _do_test_raw("""
    var x = 1;
    var y = 2;
    var z = x + y;

    var dbz = 1;
    var dbz1 = 1;
    dbz = dbz / 0;
    dbz1 = dbz1 % 0;

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

    assert _get_var(err, "dbz") == 0  # Spidermonkey does this.
    assert _get_var(err, "dbz1") == 0  # ...and this.
    assert _get_var(err, "dbz2") == 0
    assert _get_var(err, "dbz3") == 0

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

    assert _get_var(err, "x") == True
    assert _get_var(err, "y") == True
    print _get_var(err, "a"), "<<<"
    assert _get_var(err, "a") == False
    assert _get_var(err, "b") == False

def test_function_instanceof():
    """
    Test that Function can be used with instanceof operators without error.
    """

    assert not _do_test_raw("""
    var x = foo();
    print(x instanceof Function);
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    print(x === Function);
    """).failed()

