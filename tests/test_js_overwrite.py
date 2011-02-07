from js_helper import _do_test_raw

def test_new_overwrite():
    "Tests that objects created with `new` can be overwritten"

    results = _do_test_raw("""
    var x = new String();
    x += "asdf";
    x = "foo";
    """)
    assert not results.message_count

