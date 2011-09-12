from js_helper import _do_test_raw

def test_pref_innocuous_branch():
    """
    Tests that innocuous preferences created outside of the "extensions." branch
    from defaults/preferences/*.js files throw warnings, and that ones created
    in proper branches don't.
    """

    assert _do_test_raw("""
    pref("foo.bar", true);
    """, path="defaults/preferences/prefs.js").failed()

    assert _do_test_raw("""
    user_pref("foo.bar", true);
    """, path="defaults/preferences/prefs.js").failed()

    assert _do_test_raw("""
    pref("extensions.foo-bar", true);
    """, path="defaults/preferences/prefs.js").failed()

    assert not _do_test_raw("""
    pref("extensions.foo-bar.baz", true);
    """, path="defaults/preferences/prefs.js").failed()

def test_pref_dangerous_branch():
    """
    Test that preferences created in dangerous branches from
    defaults/preferences/*.js files throw warnings.
    """

    assert _do_test_raw("""
    pref("extensions.getAddons.get.url", "http://evil.com/");
    """, path="defaults/preferences/prefs.js").failed()

    assert _do_test_raw("""
    user_pref("extensions.getAddons.get.url", "http://evil.com/");
    """, path="defaults/preferences/prefs.js").failed()


def test_pref_complex_code():
    """
    Test that calls to functions other than pref() or user_pref() in default
    preference files throw warnings and that calls to pref() and user_pref()
    don't.
    """

    assert not _do_test_raw("""
    pref();
    user_pref();
    """, path="defaults/preferences/prefs.js").failed()

    assert _do_test_raw("""
    foo();
    """, path="defaults/preferences/prefs.js").failed()

    assert _do_test_raw("""
    foo.bar();
    """, path="defaults/preferences/prefs.js").failed()

