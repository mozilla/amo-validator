import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True

def _do_test(path):
    "Performs a test on a JS file"

    script = open(path).read()
    return _do_test_raw(script, path)

def _do_test_raw(script, path="foo"):
    "Performs a test on a JS file"
    
    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def _get_var(err, name):
    return err.final_context.data[name].get_literal_value()

