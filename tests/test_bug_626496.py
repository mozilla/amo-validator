import os
import validator.testcases.scripting

def _do_test(path):
    "Performs a test on a JS file"
    script = open(path).read()
    
    err = validator.testcases.scripting.traverser.MockBundler()
    try:
        validator.testcases.scripting.test_js_file(err, path, script)
    except validator.testcases.scripting.JSReflectException:
        pass

    return err

def test_control_chars():
    "Tests that control characters throw a single error"

    err = _do_test("tests/resources/bug_626496.js")
    # There should be a single error.
    print err.ids
    assert err.ids[0][2] == "retrieving_tree"

