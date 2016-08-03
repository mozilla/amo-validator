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
    assert _get_var(scope, 'a') is True
    assert _get_var(scope, 'b') is True
    assert _get_var(scope, 'c') is False
    assert _get_var(scope, 'd') is False
    assert _get_var(scope, 'e') is False
    assert _get_var(scope, 'f') is False
    assert _get_var(scope, 'g') is True
    assert _get_var(scope, 'h') is True
    assert _get_var(scope, 'i') is True
    assert _get_var(scope, 'j') is True
    assert _get_var(scope, 'k') is True
    assert _get_var(scope, 'l') is True


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
    assert _get_var(scope, 'a') is False
    assert _get_var(scope, 'b') is True
    assert _get_var(scope, 'c') is True
    assert _get_var(scope, 'd') is False
    assert _get_var(scope, 'e') is False
    assert _get_var(scope, 'f') is True

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
    assert _get_var(scope, 'a') is True
    assert _get_var(scope, 'b') is False
    assert _get_var(scope, 'c') is True
    assert _get_var(scope, 'd') is False
    assert _get_var(scope, 'e') is True
    assert _get_var(scope, 'f') is False


def test_typecasting():
    """Test that types are properly casted."""

    scope = _do_test_raw("""
    var a = 1 == '1',
        b = 255 == '0xff',
        c = 0 == '\\r';
    """)
    assert _get_var(scope, 'a') is True
    assert _get_var(scope, 'b') is True
    assert _get_var(scope, 'c') is True


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
    assert _get_var(scope, 'a') == 'truefoo'
    assert _get_var(scope, 'b') == 'footrue'
    assert _get_var(scope, 'c') == 'truefoo'
    assert _get_var(scope, 'd') == 'foofalse'
    assert _get_var(scope, 'e') == 'foo345'
    assert _get_var(scope, 'f') == 'foo-100'


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
    assert _get_var(scope, 'a') == 1
    assert _get_var(scope, 'b') == 1
    assert _get_var(scope, 'c') == 99
    assert _get_var(scope, 'd') == 99
