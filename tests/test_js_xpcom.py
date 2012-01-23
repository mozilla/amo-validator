from nose.tools import eq_

from js_helper import _do_test_raw, _do_real_test_raw


def test_xmlhttprequest():
    """Tests that the XPCOM XHR yields the standard XHR."""

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


def test_nsiaccessibleretrieval():
    """Flag any uses of nsIAccessibleRetrieval."""

    err = _do_test_raw("""
    var c = Components.classes[""].createInstance(
        Components.interfaces.nsIAccessibleRetrievalWhatever);
    """)
    eq_(len(err.warnings), 0)

    err = _do_test_raw("""
    var c = Components.classes[""].createInstance(
        Components.interfaces.nsIAccessibleRetrieval);
    """)
    eq_(len(err.warnings), 1)


def test_evalinsandbox():
    """Tests that Components.utils.evalInSandbox() is treated like eval."""

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

def test_getinterface():
    """Test the functionality of the getInterface method."""

    assert _do_test_raw("""
        obj.getInterface(Components.interfaces.nsIXMLHttpRequest)
           .open("GET", "foo", false);
    """).failed()

def test_queryinterface():
    """Test the functionality of the QueryInterface method."""

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.open("GET", "foo", false);
    """).failed()

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.QueryInterface(Components.interfaces.nsISupports);
        obj.open("GET", "foo", false);
    """).failed()

    assert _do_test_raw("""
        var obj = {};
        obj.QueryInterface(Components.interfaces.nsISupports);
        obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
        obj.open("GET", "foo", false);
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .open("GET", "foo", false);
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .QueryInterface(Components.interfaces.nsISupports)
          .open("GET", "foo", false);
    """).failed()

    assert _do_test_raw("""
        {}.QueryInterface(Components.interfaces.nsISupports)
          .QueryInterface(Components.interfaces.nsIXMLHttpRequest)
          .open("GET", "foo", false);
    """).failed()

    # TODO:
    if False:
        assert _do_test_raw("""
            var obj = {};
            obj.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
            obj.open("GET", "foo", false);
        """).failed()

        assert _do_test_raw("""
            var obj = { foo: {} };
            obj.foo.QueryInterface(Components.interfaces.nsIXMLHttpRequest);
            obj.foo.open("GET", "foo", false);
        """).failed()

def test_overwritability():
    """Test that XPCOM globals can be overwritten."""

    assert not _do_test_raw("""
    xhr = Components.classes[""].createInstance(
        Components.interfaces.nsIXMLHttpRequest);
    xhr = "foo";
    """).failed(fail_on_warnings=False)


def test_banned_interfaces():
    """Test that banned XPCOM interfaces are flagged."""

    err = _do_real_test_raw("""
    Components.classes[""].createInstance(
        Components.interfaces.nsIDOMDocumentTraversal);
    """)
    print err.print_summary(verbose=True)
    print err.compat_summary
    assert not err.failed(fail_on_warnings=False)
    assert not any(err.compat_summary.values())

    err = _do_real_test_raw("""
    Components.classes[""].createInstance(
        Components.interfaces.nsIDOMDocumentTraversal);
    """, versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": ["6.0a1"]})
    print err.print_summary(verbose=True)
    print err.compat_summary
    assert not err.failed(fail_on_warnings=False)
    assert err.compat_summary["errors"]


def _test_when_bootstrapped(code, fail_bootstrapped=True, fail=False):
    """Tests a chunk of code when the add-on is bootstrapped."""

    assert _do_test_raw(code, bootstrap=True).failed() == fail_bootstrapped
    assert _do_test_raw(code, bootstrap=False).failed() == fail


def test_xpcom_shortcut_cu():
    """Test the Components.utils shortcut."""

    assert not _do_test_raw("""
    Cu.foo();
    """).failed()

    assert _do_test_raw("""
    Cu.evalInSandbox("foo");
    """).failed()


def test_xpcom_shortcut_ci():
    """Test the Components.interfaces shortcut."""

    err = _do_test_raw("""
    var item = Components.classes["@mozilla.org/windowmediator;1"]
                         .getService(Ci.nsIWindowMediator);
    item.registerNotification();
    """, bootstrap=True)
    eq_(len(err.warnings), 1)

    err = _do_test_raw("""
    var item = Components.classes["@mozilla.org/windowmediator;1"]
                         .getService(Ci.nsIWindowMediator);
    item.registerNotification();
    """, bootstrap=False)
    eq_(len(err.warnings), 0)


def test_xpcom_shortcut_cc():
    """Test the Components.classes shortcut."""

    err = _do_test_raw("""
    var item = Cc["@mozilla.org/windowmediator;1"]
                   .getService(Components.interfaces.nsIWindowMediator);
    item.registerNotification();
    """, bootstrap=True)
    eq_(len(err.warnings), 1)

    err = _do_test_raw("""
    var item = Cc["@mozilla.org/windowmediator;1"]
                   .getService(Components.interfaces.nsIWindowMediator);
    item.registerNotification();
    """, bootstrap=False)
    eq_(len(err.warnings), 0)


def test_xpcom_shortcut_services_scriptloader():
    """Test that Services.scriptloader throws an error."""

    assert _do_test_raw("""
    Services.scriptloader;
    """).failed()

def test_xpcom_shortcut_services_wm():
    """Test that Services.wm throws a warning when bootstrapped."""

    _test_when_bootstrapped("""
    Services.wm.registerNotification();
    """)

def test_xpcom_shortcut_services_ww():
    """Test that Services.ww throws a warning when bootstrapped."""

    _test_when_bootstrapped("""
    Services.ww.addListener();
    """)


def test_xpcom_nsibrowsersearchservice():
    """
    Test that currentEngine/defaultEngine are flagged when they are
    overwritten.
    """

    assert not _do_test_raw("""
    var foo = Cc["@mozilla.org/browser/search-service;1"]
                   .getService(Components.interfaces.nsIBrowserSearchService);
    alert(foo.currentEngine);
    foo.bar = true;
    """).failed()

    assert not _do_test_raw("""
    var foo = Cc["@mozilla.org/browser/search-service;1"]
                   .getService(Components.interfaces.nsIBrowserSearchService);
    foo.currentEngine = 123;
    """).failed()

    assert not _do_test_raw("""
    var foo = Cc["@mozilla.org/browser/search-service;1"]
                   .getService(Components.interfaces.nsIBrowserSearchService);
    foo.defaultEngine = 123;
    """).failed()

