from nose.tools import eq_
from js_helper import _do_test_raw, _get_var


def test_boolean_comparison():
    """Test that true/false are properly compared."""

    scope = _do_test_raw("""
    var a = false < true,
        b = true > false,
        c = false > true,
        d = true < false,
        e = false < false,
        f = true < true,
        g = true == true,
        h = false == false,
        i = true > 0,
        j = true == 1,
        k = false < 1,
        l = false == 0;
    """)
    eq_(_get_var(scope, "a"), True)
    eq_(_get_var(scope, "b"), True)
    eq_(_get_var(scope, "c"), False)
    eq_(_get_var(scope, "d"), False)
    eq_(_get_var(scope, "e"), False)
    eq_(_get_var(scope, "f"), False)
    eq_(_get_var(scope, "g"), True)
    eq_(_get_var(scope, "h"), True)
    eq_(_get_var(scope, "i"), True)
    eq_(_get_var(scope, "j"), True)
    eq_(_get_var(scope, "k"), True)
    eq_(_get_var(scope, "l"), True)


def test_string_comparison():
    """Test that strings are properly compared."""

    scope = _do_test_raw("""
    var a = "string" < "string",
        b = "astring" < "string",
        c = "strings" < "stringy",
        d = "strings" < "stringier",
        e = "string" < "astring",
        f = "string" < "strings";
    """)
    eq_(_get_var(scope, "a"), False)
    eq_(_get_var(scope, "b"), True)
    eq_(_get_var(scope, "c"), True)
    eq_(_get_var(scope, "d"), False)
    eq_(_get_var(scope, "e"), False)
    eq_(_get_var(scope, "f"), True)

    # We can assume that the converses are true; Spidermonkey makes that easy.


def test_signed_zero():
    """Test that signed zeroes are compared properly."""

    scope = _do_test_raw("""
    var a = 0 == 0,
        b = 0 != 0,
        c = 0 == -0,
        d = 0 != -0,
        e = -0 == 0,
        f = -0 != 0;
    """)
    eq_(_get_var(scope, "a"), True)
    eq_(_get_var(scope, "b"), False)
    eq_(_get_var(scope, "c"), True)
    eq_(_get_var(scope, "d"), False)
    eq_(_get_var(scope, "e"), True)
    eq_(_get_var(scope, "f"), False)


def test_typecasting():
    """Test that types are properly casted."""

    scope = _do_test_raw("""
    var a = 1 == '1',
        b = 255 == '0xff',
        c = 0 == '\\r';
    """)
    eq_(_get_var(scope, "a"), True)
    eq_(_get_var(scope, "b"), True)
    eq_(_get_var(scope, "c"), True)


def test_additive_typecasting():
    """
    Test than additive and multiplicative expressions are evaluated properly.
    """
    scope = _do_test_raw("""
    var first = true,
        second = "foo",
        third = 345;
    var a = first + second,
        b = second + first,
        c = Boolean(true) + String("foo"),
        d = String("foo") + Boolean(false),
        e = second + third,
        f = String("foo") + Number(-100);
    """)
    eq_(_get_var(scope, "a"), "truefoo")
    eq_(_get_var(scope, "b"), "footrue")
    eq_(_get_var(scope, "c"), "truefoo")
    eq_(_get_var(scope, "d"), "foofalse")
    eq_(_get_var(scope, "e"), "foo345")
    eq_(_get_var(scope, "f"), "foo-100")


def test_addition_expressions():
    """Test that varying types are added correctly."""

    scope = _do_test_raw("""
    var a = true + false,
        b = Boolean(true) + Boolean(false);
    var x = 100,
        y = -1;
    var c = x + y,
        d = Number(x) + Number(y);
    """)
    eq_(_get_var(scope, "a"), 1)
    eq_(_get_var(scope, "b"), 1)
    eq_(_get_var(scope, "c"), 99)
    eq_(_get_var(scope, "d"), 99)

