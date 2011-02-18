from js_helper import _do_test_raw

def test_new_overwrite():
    "Tests that objects created with `new` can be overwritten"

    results = _do_test_raw("""
    var x = new String();
    x += "asdf";
    x = "foo";
    """)
    assert not results.message_count

def test_redefine_new_instance():
    "Test the redefinition of an instance of a global type."

    results = _do_test_raw("""
    var foo = "asdf";
    var r = new RegEx(foo, "i");
    r = new RegExp(foo, "i");
    r = null;
    """)
    assert not results.message_count
