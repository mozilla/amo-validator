from nose.tools import eq_
from js_helper import _do_test_raw, _get_var


def test_multiple_assignments():
    "Tests that multiple variables can be assigned in one sitting"

    results = _do_test_raw("""
    var x = 1, y = 2, z = 3;
    """)
    assert not results.failed()
    assert _get_var(results, "x") == 1
    assert _get_var(results, "y") == 2
    assert _get_var(results, "z") == 3


def test_arraypattern_assignment():
    "Tests that array patterns can be used to assign variables"

    results = _do_test_raw("""
    var [x, y, z] = [1, 2, 3];
    """)
    assert not results.failed()
    assert _get_var(results, "x") == 1
    assert _get_var(results, "y") == 2
    assert _get_var(results, "z") == 3


def test_objectpattern_assignment():
    "Tests that ObjectPatterns are respected"

    results = _do_test_raw("""
    var foo = {a:3,b:4,c:5};
    var {a:x, b:y, c:z} = foo;
    """)
    assert not results.failed()
    assert _get_var(results, "x") == 3
    assert _get_var(results, "y") == 4
    assert _get_var(results, "z") == 5

    results = _do_test_raw("""
    var foo = {
        a:1,
        b:2,
        c:{
            d:4
        }
    };
    var {a:x, c:{d:y}} = foo;
    """)
    assert not results.failed()
    assert _get_var(results, "x") == 1
    assert _get_var(results, "y") == 4


def test_lazy_object_member_assgt():
    """
    Test that members of lazy objects can be assigned, even if the lazy object
    hasn't yet been created.
    """

    results = _do_test_raw("""
    foo.bar = "asdf";
    zap.fizz.buzz = 123;
    var a = foo.bar,
        b = zap.fizz.buzz;
    """)
    assert not results.failed()
    eq_(_get_var(results, "a"), "asdf")
    eq_(_get_var(results, "b"), 123)

