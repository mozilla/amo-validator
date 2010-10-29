import os
import validator.testcases.scripting

def _do_test(path):
    "Performs a test on a JS file"
    
    script = open(path).read()

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def test_redefinition():
    "Tests that global objects can't be redefined"
    
    err = _do_test("tests/resources/bug_538016.js")
    # There should be eight errors.
    assert err.message_count == 8
    

