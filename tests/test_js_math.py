import math

from js_helper import _do_test_scope


INFINITY = float('inf')
NEG_INFINITY = float('-inf')


def test_abs():
    """Test that the abs() function works properly."""
    _do_test_scope("""
    var a = Math.abs(-5),
        b = Math.abs(5),
        c = Math.abs(-Infinity);
    """, {"a": 5,
          "b": 5,
          "c": INFINITY})

def test_exp():
    """Test that the exp() function works properly."""
    _do_test_scope("""
    var a = Math.exp(null),
        b = Math.exp(1) == Math.E,
        c = Math.exp(false),
        d = Math.exp('1') == Math.E,
        e = Math.exp('0'),
        f = Math.exp(0),
        g = Math.exp(-0),
        h = Math.exp(Infinity) == Infinity,
        i = Math.exp(-Infinity) == 0;

    """, {"a": 1,
          "b": True,
          "c": 1,
          "d": True,
          "e": 1,
          "f": 1,
          "g": 1,
          "h": True,
          "i": True})


def test_ceil():
    """Test that the feil() function works properly."""
    _do_test_scope("""
    var a = Math.ceil(null),
        b = Math.ceil(void 0),
        c = Math.ceil(true),
        d = Math.ceil(false),
        e = Math.ceil('1.1'),
        f = Math.ceil('-1.1'),
        g = Math.ceil('0.1'),
        h = Math.ceil('-0.1'),
        i = Math.ceil(0),
        // j = Math.ceil(-0),
        k = Math.ceil(-0) == -Math.floor(0),
        l = Math.ceil(Infinity),
        m = Math.ceil(Infinity) == -Math.floor(-Infinity),
        n = Math.ceil(-Infinity),
        o = Math.ceil(0.0000001),
        p = Math.ceil(-0.0000001);
    """, {"a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 2,
          "f": -1,
          "g": 1,
          "h": 0,
          "i": 0,
          # "j": -0,
          "k": True,
          "l": INFINITY,
          "m": True,
          "n": NEG_INFINITY,
          "o": 1,
          "p": 0})


def test_floor():
    """Test that the floor() function works properly."""
    _do_test_scope("""
    var a = Math.floor(null),
        b = Math.floor(void 0),
        c = Math.floor(true),
        d = Math.floor(false),
        e = Math.floor('1.1'),
        f = Math.floor('-1.1'),
        g = Math.floor('0.1'),
        h = Math.floor('-0.1'),
        i = Math.floor(0),
        // j = Math.floor(-0),
        k = Math.floor(-0) == -Math.ceil(0),
        l = Math.floor(Infinity),
        m = Math.floor(Infinity) == -Math.ceil(-Infinity),
        n = Math.floor(-Infinity),
        o = Math.floor(0.0000001),
        p = Math.floor(-0.0000001);
    """, {"a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 1,
          "f": -2,
          "g": 0,
          "h": -1,
          "i": 0,
          # "j": -0,
          "k": True,
          "l": INFINITY,
          "m": True,
          "n": NEG_INFINITY,
          "o": 0,
          "p": -1})


def test_trig():
    """Test the trigonometric functions."""

    _do_test_scope("""
    var pi = Math.PI;
    var cos_a = Math.cos(0),
        cos_b = Math.cos(Math.PI);
    var sin_a = Math.sin(0),
        sin_b = Math.sin(Math.PI);
    var tan_a = Math.tan(0),
        tan_b = Math.tan(Math.PI / 4);
    var acos_a = Math.acos(0) == Math.PI / 2,
        acos_b = Math.acos(1),
        acos_c = Math.acos(-1) == Math.PI;
    var asin_a = Math.asin(0),
        asin_b = Math.asin(1) == Math.PI / 2,
        asin_c = Math.asin(-1) == Math.PI / -2;
    var atan_a = Math.atan(0),
        atan_b = Math.atan(1) == Math.PI / 4,
        atan_c = Math.atan(Infinity) == Math.PI / 2;
    var atan2_a = Math.atan2(1, 0) == Math.PI / 2,
        atan2_b = Math.atan2(0, 0),
        atan2_c = Math.atan2(0, -1) == Math.PI;
    """, {"cos_a": 1,
          "cos_b": -1,
          "sin_a": 0,
          "sin_b": 0,
          "tan_a": 0,
          "tan_b": 1,
          "acos_a": True,
          "acos_b": 0,
          "acos_c": True,
          "asin_a": 0,
          "asin_b": True,
          "asin_c": True,
          "atan_a": 0,
          "atan_b": True,
          "atan_c": True,
          "atan2_a": True,
          "atan2_b": 0,
          "atan2_c": True})


def test_sqrt():
    """Test that the sqrt() function works properly."""

    _do_test_scope("""
    var a = Math.sqrt(10),
        b = Math.sqrt(4),
        c = Math.sqrt(3*3 + 4*4) == 5;
    """, {"a": round(math.sqrt(10), 5),
          "b": 2,
          "c": True})


def test_round():
    """Test that the round() function works properly."""

    _do_test_scope("""
    var a = Math.round('0.99999'),
        b = Math.round(0),
        c = Math.round(0.49),
        d = Math.round(0.5),
        e = Math.round(0.51),
        f = Math.round(-0.49),
        g = Math.round(-0.5),
        h = Math.round(-0.51);
    """, {"a": 1,
          "b": 0,
          "c": 0,
          "d": 1,
          "e": 1,
          "f": 0,
          "g": 0,
          "h": -1})


def test_random():
    """Test that the random() function works "properly"."""

    _do_test_scope("""
    var r = Math.random();
    """, {"r": 0.5})


def test_pow():
    """Test that the pow() function works properly."""

    _do_test_scope("""
    var a = Math.pow(true, false),
        b = Math.pow(2, 32),
        c = Math.pow(1.0000001, Infinity),
        d = Math.pow(1.0000001, -Infinity),
        e = Math.pow(123, 0);
    """, {"a": 1,
          "b": 4294967296,
          "c": INFINITY,
          "d": 0,
          "e": 1})


def test_log():
    """Test that the log() function works properly."""

    _do_test_scope("""
    var a = Math.log(1),
        b = Math.log(0),
        c = Math.log(Infinity),
        d = Math.log(-1);
    """, {"a": 0,
          "b": NEG_INFINITY,
          "c": INFINITY,
          "d": ''})


def test_min_max():
    """Test that the min() and max() function works properly."""

    _do_test_scope("""
    var min_a = Math.min(Infinity, -Infinity),
        min_b = Math.min(1, -1);
    var max_a = Math.max(Infinity, -Infinity),
        max_b = Math.max(1, -1);
    """, {"min_a": NEG_INFINITY,
          "min_b": -1,
          "max_a": INFINITY,
          "max_b": 1})

