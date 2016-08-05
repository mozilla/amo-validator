from js_helper import _do_test_raw, _get_var


def test_createElement():
    'Tests that createElement and createElementNS throw errors.'

    err = _do_test_raw("""
    var x = foo;
    foo.bar.whateverElement("script");
    """)
    assert not err.message_count

    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElement("scr"+"ipt");
    """)
    assert err.message_count == 1

    # Part of bug 636835
    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElement("scRipt");
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

    err = _do_test_raw("""
    document.createElement("style");
    function x(doc) {
        doc.createElement("style");
    }""")
    assert not err.message_count

    err = _do_test_raw("""
    document.createElement("sty"+"le");
    var x = "sty";
    x += "le";
    document.createElement(x);
    """)
    assert not err.message_count

    # Also test an empty call (tests for tracebacks)
    _do_test_raw("""
    document.createElement();
    """)


def test_enablePrivilege():
    """Tests that enablePrivilege throws a warning."""

    err = _do_test_raw("""
        netscape.security.PrivilegeManager.enablePrivilege()
    """)
    assert err.warnings

    assert err.warnings[0]['id'] == ('js', 'traverser', 'dangerous_global')
    assert err.warnings[0]['signing_severity'] == 'high'


def test_privileged_unprivileged_interaction():
    """Tests that functions which may lead to privilege escalation are
    detected."""

    for meth in 'cloneInto', 'exportFunction':
        err = _do_test_raw("""
            Cu.%s(foo)
        """ % meth)
        assert err.warnings

        assert err.warnings[0]['id'] == ('js', 'traverser', 'dangerous_global')
        assert err.warnings[0]['signing_severity'] == 'low'

    for form in ('var obj = { __exposedProps__: {} };',
                 'var obj = {}; obj.__exposedProps__ = {};'):
        err = _do_test_raw(form)
        assert err.warnings
        assert err.warnings[0]['signing_severity'] == 'high'


def test_synchronous_xhr():
    'Tests that syncrhonous AJAX requests are marked as dangerous'

    err = _do_test_raw("""
    var x = new XMLHttpRequest();
    x.open("GET", "http://foo/bar", true);
    x.send(null);
    """)
    assert not err.message_count

    err = _do_test_raw("""
    var x = new XMLHttpRequest();
    x.open("GET", "http://foo/bar", false);
    x.send(null);
    """)
    assert err.message_count


def test_bug652577_loadOverlay():
    """Make sure that loadOverlay is dangerous."""

    assert _do_test_raw("""
    document.loadOverlay();
    """).failed()

    assert _do_test_raw("""
    document.loadOverlay("foobar");
    """).failed()

    assert not _do_test_raw("""
    document.loadOverlay("chrome:foo/bar/");
    """).failed()

    assert not _do_test_raw("""
    document.loadOverlay("chr" + "ome:foo/bar/");
    """).failed()

    assert not _do_test_raw("""
    document.loadOverlay("resource:foo/bar/");
    """).failed()


def test_extraneous_globals():
    """Globals should not be registered from function parameters."""

    err = _do_test_raw("""
    var f = function(foo, bar) {
        foo = "asdf";
        bar = 123;
    };
    """)
    assert not err.failed()
    assert 'foo' not in err.final_context.data
    assert 'bar' not in err.final_context.data


def test_number_global_conversions():
    """Test that the Number global constructor functions properly."""
    err = _do_test_raw("""
    var a = Number(),
        b = Number(123),
        c = Number(123.123),
        d = Number("123"),
        e = Number("123.456"),
        f = Number("foo"),
        g = Number(null),
        nan = window.NaN;
    """)
    assert not err.failed()
    assert _get_var(err, 'a') == 0
    assert _get_var(err, 'b') == 123
    assert _get_var(err, 'c') == 123.123
    assert _get_var(err, 'd') == 123
    assert _get_var(err, 'e') == 123.456
    assert _get_var(err, 'f') == _get_var(err, 'nan')
    assert _get_var(err, 'g') == _get_var(err, 'nan')


def test_unsafe_template_methods():
    """Test that the use of unsafe template methods is flagged."""

    assert _do_test_raw("""bar = Handlebars.SafeString(foo)""").failed()
    assert _do_test_raw("""bar = $sce.trustAsHTML(foo)""").failed()
    assert _do_test_raw("""bar = $sce.trustAs("html", foo)""").failed()
