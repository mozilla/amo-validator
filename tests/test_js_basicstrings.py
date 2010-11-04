import os
import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True

def _do_test(path):
    "Performs a test on a JS file"
    
    script = open(path).read()

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def _get_var(err, name):
    return err.final_context.data[name].get_literal_value()

def test_basic_math():
    "Tests that contexts work and that basic math is executed properly"
    
    err = _do_test("tests/resources/javascript/basicstrings.js")
    assert err.message_count == 0
    
    assert _get_var(err, "x") == "foo"
    assert _get_var(err, "y") == "bar"
    assert _get_var(err, "z") == "foobar"
    assert _get_var(err, "a") == "5"
    assert _get_var(err, "b") == "6"
    assert _get_var(err, "c") == "56"
    assert _get_var(err, "d") == 1
    assert _get_var(err, "e") == 30
    assert _get_var(err, "f") == 5


