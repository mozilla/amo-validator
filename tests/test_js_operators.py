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
    
    err = _do_test("tests/resources/javascript/operators.js")
    assert err.message_count == 0
    
    assert _get_var(err, "x") == 1
    assert _get_var(err, "y") == 2
    assert _get_var(err, "z") == 3
    assert _get_var(err, "a") == 5
    assert _get_var(err, "b") == 4
    assert _get_var(err, "c") == 8

def test_in_operator():
    "Tests the 'in' operator."

    err = _do_test("tests/resources/javascript/in_operator.js")
    assert err.message_count == 0
    print err.final_context.output()

    print _get_var(err, "x"), "<<<"
    assert _get_var(err, "x") == True
    assert _get_var(err, "y") == True
    assert _get_var(err, "a") == False
    assert _get_var(err, "b") == False


