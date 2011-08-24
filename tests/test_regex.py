from helper import MockXPI
from js_helper import _do_real_test_raw as _do_test_raw
from validator.decorator import version_range
from validator.errorbundler import ErrorBundle
import validator.testcases.content
import validator.testcases.regex as regex_tests


def test_valid():
    "Tests a valid string in a JS bit"
    assert not _do_test_raw("var x = 'network.foo';").failed()


def test_basic_regex_fail():
    "Tests that a simple Regex match causes a warning"

    assert _do_test_raw("var x = 'network.http';").failed()
    assert _do_test_raw("var x = 'extensions.foo.update.url';").failed()
    assert _do_test_raw("var x = 'network.websocket.foobar';").failed()
    assert _do_test_raw("var x = 'browser.preferences.instantApply';").failed()

    err = ErrorBundle()
    err.supported_versions = {}
    result = validator.testcases.content._process_file(
            err, MockXPI(), "foo.xml",
            """
            All I wanna do is browser.preferences.instantApply() to you
            """)
    assert result
    assert err.failed()


def test_js_category_regex_fail():
    "Tests that JS category registration causes a warning"

    assert _do_test_raw("addCategory('JavaScript global property')").failed()
    assert _do_test_raw("addCategory('JavaScript-global-property')").failed()


def test_dom_mutation_fail():
    """Test that DOM mutation events raise a warning."""

    assert not _do_test_raw("foo.DOMAttr = bar;").failed()
    assert _do_test_raw("foo.DOMAttrModified = bar;").failed()


def test_bug_548645():
    "Tests that banned entities are disallowed"

    results = _do_test_raw("""
    var y = newThread;
    var x = foo.newThread;
    var w = foo["newThread"];
    """)
    print results.print_summary(verbose=True)
    assert ((len(results.errors) + len(results.warnings) +
             len(results.notices)) == 3)


def test_processNextEvent_banned():
    """Test that processNextEvent is properly banned."""

    assert not _do_test_raw("""
    foo().processWhatever();
    var x = "processNextEvent";
    """).failed()

    assert _do_test_raw("""
    foo().processNextEvent();
    """).failed()

    assert _do_test_raw("""
    var x = "processNextEvent";
    foo[x]();
    """).failed()


def test_bug_652575():
    """Ensure that capability.policy gets flagged."""
    assert _do_test_raw("var x = 'capability.policy';").failed()


def test_app_update_timer():
    """Flag instances of app.update.timer in compatibility."""

    err = _do_test_raw("""
    var f = app.update.timer;
    """)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_test_raw("""
    var f = app.update.timer;
    """, versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                       version_range("firefox", "6.0a1")})
    assert not err.failed()
    assert err.compat_summary["errors"]


def test_incompatible_uris():
    """Flag instances of javascript:/data: in compatibility."""

    fx6 = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
               version_range("firefox", "6.0a1")}

    err = _do_test_raw("""
    var f = "javascript:foo();";
    """)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = ErrorBundle()
    err.supported_versions = fx6
    regex_tests.run_regex_tests("""
    var f = "javascript:foo();";
    """, err, "foo.bar", is_js=False)
    assert not err.failed()
    assert not any(err.compat_summary.values())

    err = _do_test_raw("""
    var f = "javascript:foo();";
    """, versions=fx6)
    assert not err.failed()
    assert err.compat_summary["warnings"]

    err = _do_test_raw("""
    var f = "data:foo();";
    """, versions=fx6)
    assert not err.failed()
    assert err.compat_summary["warnings"]

    err = _do_test_raw("""
    var foo = "postdata:LOL NOT THE CASE";
    """, versions=fx6)
    assert not err.failed()
    assert not any(err.compat_summary.values())

