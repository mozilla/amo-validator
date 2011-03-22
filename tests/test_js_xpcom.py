from js_helper import _do_test_raw

def test_xmlhttprequest():
    "Tests that the XPCOM XHR yields the standard XHR"

    err = _do_test_raw("""
    // Accessing a member on Components.classes is a wildcard
    var class_ = Components.interfaces.nsIXMLHttpRequest;
    var req = Components.classes["foo.bar"]
                        .createInstance(class_);
    """)
    print "XHR Class:", err.final_context.get("class_").value
    req = err.final_context.get("req").value
    print "Req:", req

    assert "value" in req
    assert "open" in req["value"]

def test_evalinsandbox():
    "Tests Components.utils.evalInSandbox()"

    err = _do_test_raw("""
    var Cu = Components.utils;
    Cu.foo("bar");
    """)
    assert not err.failed()

    err = _do_test_raw("""
    var Cu = Components.utils;
    Cu.evalInSandbox("foo");
    """)
    assert err.failed()

    err = _do_test_raw("""
    const Cu = Components.utils;
    Cu.evalInSandbox("foo");
    """)
    assert err.failed()

def test_queryinterface():
    "Tests the functionality of the getInterface method"

    assert _do_test_raw("""
        obj.getInterface(Components.interfaces.nsIXMLHttpRequest)
           .open("GET");
    """).failed()

def test_queryinterface():
    "Tests the functionality of the QueryInterface method"

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.open("GET");
    """).failed()

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.QueryInterface(Components.interfaces.nsISupports);
        obj.open("GET");
    """).failed()

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsISupports);
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.open("GET");
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .open("GET");
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .QueryInterface(Components.interfaces.nsISupports)
          .open("GET");
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsISupports)
          .QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .open("GET");
    """).failed()

    # TODO:
    if False:
        assert _do_test_raw("""
            var obj = {};
            obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
            obj.open("GET");
        """).failed()

        assert _do_test_raw("""
            var obj = { foo: {} };
            obj.foo.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
            obj.foo.open("GET");
        """).failed()

