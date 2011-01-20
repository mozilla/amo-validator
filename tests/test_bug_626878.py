import os
import validator.testcases.scripting

def _do_test(path):
    "Performs a test on a JS file"
    script = open(path).read()
    
    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def test_double_escaped():
    "Tests that escaped characters don't result in errors"

    err = _do_test("tests/resources/bug_626878.js")
    assert not err.message_count

