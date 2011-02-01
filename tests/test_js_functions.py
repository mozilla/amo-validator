import os
import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True

def _do_test_raw(script):
    "Performs a test on a JS file"
    
    path = "foo"

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def _get_var(err, name):
    return err.final_context.data[name].get_literal_value()

def test_createElement():
    "Tests that createElement and createElementNS throw errors."
    
    err = _do_test_raw("""
    var x = foo;
    foo.bar.whateverElement("script");
    """)
    assert err.message_count == 0

    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElement("scr"+"ipt");
    """)
    assert err.message_count == 1
    
    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElementNS("http://foo.bar/", "asdf:" +"scr"+"ipt");
    """)
    assert err.message_count == 1

    err = _do_test_raw("""
    let scr = "scr";
    scr += "ipt";
    foo.bar.createElement(scr);
    """)
    assert err.message_count == 1

