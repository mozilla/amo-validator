import os
import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True

def _do_test(path):
    "Performs a test on a JS file"
    
    script = open(path).read()

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def test_no_dups():
    "Tests that errors are not duplicated."
    
    err = _do_test("tests/resources/javascript/dups.js")
    assert err.message_count == 5

