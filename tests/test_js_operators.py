from nose.tools import eq_
from js_helper import _do_real_test_raw, _do_test_raw, _do_test_scope, _get_var


def test_assignment_with_pollution():
    """
    Access a bunch of identifiers, but do not write to them. Accessing
    undefined globals should not create scoped objects.
    """
    assert not _do_real_test_raw("""
    var x = "";
    x = foo;
    x = bar;
    x = zap;
    x = baz; // would otherwise cause pollution errors.
    """).failed()


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


def test_unary_typeof():
    """Test that the typeof operator does good."""

    scope = _do_test_raw("""
    var a = typeof(void(0)),
        b = typeof(null),
        c = typeof(true),
        d = typeof(false),
        e = typeof(new Boolean()),
        f = typeof(new Boolean(true)),
        g = typeof(Boolean()),
        h = typeof(Boolean(false)),
        i = typeof(Boolean(true)),
        j = typeof(NaN),
        k = typeof(Infinity),
        l = typeof(-Infinity),
        m = typeof(Math.PI),
        n = typeof(0),
        o = typeof(1),
        p = typeof(-1),
        q = typeof('0'),
        r = typeof(Number()),
        s = typeof(Number(0)),
        t = typeof(new Number()),
        u = typeof(new Number(0)),
        v = typeof(new Number(1)),
        x = typeof(function() {}),
        y = typeof(Math.abs);
    """)
    eq_(_get_var(scope, "a"), "undefined")
    eq_(_get_var(scope, "b"), "object")
    eq_(_get_var(scope, "c"), "boolean")
    eq_(_get_var(scope, "d"), "boolean")
    eq_(_get_var(scope, "e"), "object")
    eq_(_get_var(scope, "f"), "object")
    eq_(_get_var(scope, "g"), "boolean")
    eq_(_get_var(scope, "h"), "boolean")
    eq_(_get_var(scope, "i"), "boolean")
    # TODO: Implement "typeof" for predefined entities
    # eq_(_get_var(scope, "j"), "number")
    # eq_(_get_var(scope, "k"), "number")
    # eq_(_get_var(scope, "l"), "number")
    eq_(_get_var(scope, "m"), "number")
    eq_(_get_var(scope, "n"), "number")
    eq_(_get_var(scope, "o"), "number")
    eq_(_get_var(scope, "p"), "number")
    eq_(_get_var(scope, "q"), "string")
    eq_(_get_var(scope, "r"), "number")
    eq_(_get_var(scope, "s"), "number")
    eq_(_get_var(scope, "t"), "object")
    eq_(_get_var(scope, "u"), "object")
    eq_(_get_var(scope, "v"), "object")
    eq_(_get_var(scope, "x"), "function")
    eq_(_get_var(scope, "y"), "function")


# TODO(basta): Still working on the delete operator...should be done soon.

#def test_delete_operator():
#    """Test that the delete operator works correctly."""
#
#    # Test that array elements can be destroyed.
#    eq_(_get_var(_do_test_raw("""
#    var x = [1, 2, 3];
#    delete(x[2]);
#    var value = x.length;
#    """), "value"), 2)
#
#    # Test that hte right array elements are destroyed.
#    eq_(_get_var(_do_test_raw("""
#    var x = [1, 2, 3];
#    delete(x[2]);
#    var value = x.toString();
#    """), "value"), "1,2")
#
#    eq_(_get_var(_do_test_raw("""
#    var x = "asdf";
#    delete x;
#    var value = x;
#    """), "value"), None)
#
#    assert _do_test_raw("""
#    delete(Math.PI);
#    """).failed()


def test_logical_not():
    """Test that logical not is evaluated properly."""

    scope = _do_test_raw("""
    var a = !(null),
        // b = !(var x),
        c = !(void 0),
        d = !(false),
        e = !(true),
        // f = !(),
        g = !(0),
        h = !(-0),
        // i = !(NaN),
        j = !(Infinity),
        k = !(-Infinity),
        l = !(Math.PI),
        m = !(1),
        n = !(-1),
        o = !(''),
        p = !('\\t'),
        q = !('0'),
        r = !('string'),
        s = !(new String('')); // This should cover all type globals.
    """)
    eq_(_get_var(scope, "a"), True)
    # eq_(_get_var(scope, "b"), True)
    eq_(_get_var(scope, "c"), True)
    eq_(_get_var(scope, "d"), True)
    eq_(_get_var(scope, "e"), False)
    # eq_(_get_var(scope, "f"), True)
    eq_(_get_var(scope, "g"), True)
    eq_(_get_var(scope, "h"), True)
    # eq_(_get_var(scope, "i"), True)
    eq_(_get_var(scope, "j"), False)
    eq_(_get_var(scope, "k"), False)
    eq_(_get_var(scope, "l"), False)
    eq_(_get_var(scope, "m"), False)
    eq_(_get_var(scope, "n"), False)
    eq_(_get_var(scope, "o"), True)
    eq_(_get_var(scope, "p"), False)
    eq_(_get_var(scope, "q"), False)
    eq_(_get_var(scope, "r"), False)
    eq_(_get_var(scope, "s"), False)


def test_concat_plus_infinity():
    """Test that Infinity is concatenated properly."""
    _do_test_scope("""
    var a = Infinity + "foo",
        b = (-Infinity) + "foo",
        c = "foo" + Infinity,
        d = "foo" + (-Infinity);
    """, {"a": "Infinityfoo",
          "b": "-Infinityfoo",
          "c": "fooInfinity",
          "d": "foo-Infinity"})

