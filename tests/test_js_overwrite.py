from js_helper import _do_test_raw, _get_var


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


def test_property_members():
    "Tests that properties and members are treated fairly"

    results = _do_test_raw("""
    var x = {"foo":"bar"};
    var y = x.foo;
    var z = x["foo"];
    """)
    assert _get_var(results, "y") == "bar"
    assert _get_var(results, "z") == "bar"


def test_bug621106():
    "Tests that important objects cannot be overridden by JS"

    assert _do_test_raw("""
    Number.prototype = "This is the new prototype";
    """).failed()

    assert _do_test_raw("""
    Object.prototype.test = "bar";
    """).failed()

    assert _do_test_raw("""
    Object = "asdf";
    """).failed()

    assert _do_test_raw("""
    var x = Object.prototype;
    x.test = "asdf";
    """).failed()


def test_with_statement():
    "Tests that 'with' statements work as intended"

    err = _do_test_raw("""
    var x = {"foo":"bar"};
    with(x) {
        foo = "zap";
    }
    var z = x["foo"];
    """)
    assert not err.failed()

    print _get_var(err, "z")
    assert _get_var(err, "z") == "zap"


    # Assert that the contets of a with statement are still evaluated even
    # if the context object is not available.
    err = _do_test_raw("""
    with(foo.bar) { // These do not exist yet
        eval("evil");
    }
    """)
    assert err.failed()


def test_local_global_overwrite():
    """Test that a global assigned to a local variable can be overwritten."""
    err = _do_test_raw("""
    foo = String.prototype;
    foo = "bar";
    """)
    assert not err.failed()


def test_overwrite_global():
    """Test that an overwriteable global is overwriteable."""
    assert not _do_test_raw("""
    document.title = "This is something that isn't a global";
    """).failed()

def test_overwrite_readonly_false():
    """Test that globals with readonly set to false are overwriteable."""
    assert not _do_test_raw("""
    window.innerHeight = 123;
    """).failed()

