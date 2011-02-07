from js_helper import _do_test, _get_var

def test_basic_math():
    "Tests that contexts work and that basic math is executed properly"
    
    err = _do_test("tests/resources/javascript/operators.js")
    assert err.message_count == 0
    
    assert _get_var(err, "x") == 1
    assert _get_var(err, "y") == 2
    assert _get_var(err, "z") == 3
    assert _get_var(err, "a") == 5
    assert _get_var(err, "b") == 4
    assert _get_var(err, "c") == 8


