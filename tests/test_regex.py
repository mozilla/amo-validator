from mock import Mock
from nose.tools import eq_

from helper import MockXPI
from js_helper import _do_real_test_raw as _do_test_raw
from validator.decorator import version_range
from validator.errorbundler import ErrorBundle
from validator.compat import (TB11_DEFINITION, TB12_DEFINITION)
from validator.testcases import regex
from validator.testcases.regex import RegexTest
import validator.testcases.content


def test_valid():
    "Tests a valid string in a JS bit"
    assert not _do_test_raw("var x = 'network.foo';").failed()

def test_marionette_preferences_and_references_fail():
    "Tests that check for marionette. Added in bug 741812"

    _dtr = lambda script: _do_test_raw(script, path='defaults/preferences/foo.js')

    assert _dtr("var x = 'marionette.defaultPrefs.port';").failed()
    assert _dtr("var x = 'marionette.defaultPrefs.enabled';").failed()
    assert _dtr("var x = 'marionette.force-local';").failed()
    assert _dtr("var x = '@mozilla.org/marionette;1';").failed()
    assert _dtr("var x = '{786a1369-dca5-4adc-8486-33d23c88010a}';").failed()
    assert _dtr("var x = 'MarionetteComponent';").failed()
    assert _dtr("var x = 'MarionetteServer';").failed()

def test_not_marionette_preferences_and_references_pass():
    "Tests that check for marionette. Added in bug 741812"

    assert not _do_test_raw("var x = 'marionette.defaultPrefs.port';").failed()
    assert not _do_test_raw("var x = 'marionette.defaultPrefs.enabled';").failed()
    assert not _do_test_raw("var x = 'marionette.force-local';").failed()
    assert not _do_test_raw("var x = '@mozilla.org/marionette;1';").failed()
    assert not _do_test_raw("var x = '{786a1369-dca5-4adc-8486-33d23c88010a}';").failed()
    assert not _do_test_raw("var x = 'MarionetteComponent';").failed()
    assert not _do_test_raw("var x = 'MarionetteServer';").failed()

def test_basic_regex_fail():
    "Tests that a simple Regex match causes a warning"

    assert _do_test_raw("var x = 'network.http.';").failed()
    assert _do_test_raw("var x = 'extensions.foo.update.url';").failed()
    assert _do_test_raw("var x = 'network.websocket.foobar';").failed()
    assert _do_test_raw("var x = 'browser.preferences.instantApply';").failed()
    assert _do_test_raw("var x = 'nglayout.debug.disable_xul_cache';").failed()

    err = ErrorBundle()
    err.supported_versions = {}
    validator.testcases.content._process_file(
        err, MockXPI(), "foo.hbs",
        "All I wanna do is <%= interpolate %> to you",
        "foo.hbs")
    assert err.failed()


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
    assert (len(results.errors) + len(results.warnings) +
            len(results.notices)) == 3


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


def test_extension_manager_api():
    assert _do_test_raw("""
    Cc["@mozilla.org/extensions/manager;1"].getService();
    """).failed()

    assert _do_test_raw("""
    if (topic == "em-action-requested") true;
    """).failed()

    assert _do_test_raw("""
    thing.QueryInterface(Ci.nsIExtensionManager);
    """).failed()


def test_bug_652575():
    """Ensure that capability.policy gets flagged."""
    assert _do_test_raw("var x = 'capability.policy.';").failed()


def test_app_update_timer():
    """Flag instances of app.update.timer in compatibility."""

    err = _do_test_raw("""
    var f = app.update.timer;
    """)
    assert not any(err.compat_summary.values())

    err = _do_test_raw("""
    var f = app.update.timer;
    """, versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                       version_range("firefox", "6.0a1")})
    assert err.warnings
    assert err.compat_summary["errors"]


def test_chrome_usage():

    def base_case():
        err = _do_test_raw("""var foo = require("bar");""")
        eq_(err.metadata['requires_chrome'], False)
    yield base_case

    interfaces = ["chrome", "window-utils", "observer-service"]

    def interface_cases(interface):
        err = _do_test_raw("""var {cc, ci} = require("%s")""" % interface)
        print err.print_summary(verbose=True)

        first_message = err.warnings[0]['message']
        assert 'non-SDK interface' in first_message, ('unexpected: %s' %
                                                          first_message)
        assert 'requires_chrome' in err.metadata, \
                'unexpected: "requires_chrome" should be in metadata'
        eq_(err.metadata['requires_chrome'], True)

    for case in interfaces:
        yield lambda: interface_cases(case)


def test_preference_extension_regex():
    """Test that preference extension regexes pick up the proper strings."""

    assert not _do_test_raw('"chrome://mozapps/skin/extensions/update1.png"').failed()
    assert _do_test_raw('"extensions.update.bar"').failed()


def test_template_escape():
    """Tests that the use of unsafe template escape sequences is flagged."""

    assert _do_test_raw("<%= foo %>").failed()
    assert _do_test_raw("{{{ foo }}}").failed()

    assert _do_test_raw("ng-bind-html-unsafe='foo'").failed()


def test_tb11_strings():
    """Flag changed or removed strings in add-on code"""

    err = _do_test_raw("""
    var f = "newToolbarCmd.tooltip";
    var x = "onViewToolbarCommand";
    """, versions=TB11_DEFINITION)
    assert err.failed()
    assert err.warnings
    assert err.notices
    assert err.compat_summary["errors"]


def test_tb12_strings():
    """Flag changed or removed strings in add-on code"""

    err = _do_test_raw("""
    var f = "editImageMapButton.label";
    var x = "haveSmtp1.suffix2";
    """, versions=TB12_DEFINITION)
    assert err.failed()
    assert err.warnings
    assert err.notices
    assert err.compat_summary["errors"]


def test_servicessync():
    """
    Test that instances of `resource://services-sync` are flagged due to their
    volatile nature.
    """

    err = _do_test_raw("""
    var r = "resource://services-sync";
    """)
    assert err.failed()
    assert err.warnings
    assert not any(val for k, val in err.compat_summary.items())


def test_mouseevents():
    """Test that mouse events are properly handled."""

    err = _do_test_raw("window.addEventListener('mousemove', func);")
    assert err.warnings


def test_munge_filename():
    """Tests that the munge_filename function has the expected results."""

    eq_(regex.munge_filename("foo.bar"), r"foo\.bar"),
    eq_(regex.munge_filename("foo.bar/*"), r"foo\.bar(?:[/\\].*)?")


class TestRegexTest(object):
    def test_process_key(self):
        """Tests that the process_key method behaves as expected."""

        key = RegexTest(()).process_key

        # Test that plain strings stay unmolested
        string = r"foo\*+?.|{}[]()^$"
        eq_(key(string), string)

        # Test that tuples are converted to expected full-string regexps
        eq_(key(("foo",)), r"^(?:foo)$")

        eq_(key(("foo", "bar")), r"^(?:foo|bar)$")

        eq_(key((r"foo\*+?.|{}[]()^$", "bar")),
            r"^(?:foo\\\*\+\?\.\|\{\}\[\]\(\)\^\$|bar)$")

    def test_glomming(self):
        """Tests that multiple regular expressions are glommed together
        properly."""

        def expect(keys, val):
            eq_(RegexTest(tuple((key, {}) for key in keys)).regex_source,
                val)

        expect(["foo"], r"(?P<test_0>foo)")

        expect([r"foo\|\**"], r"(?P<test_0>foo\|\**)")

        expect(("foo", "bar"), r"(?P<test_0>foo)|(?P<test_1>bar)")

        expect((r"foo\|\**", "bar"), r"(?P<test_0>foo\|\**)|(?P<test_1>bar)")

    def test_multiple_warnings(self):
        """Tests that multiple warnings are emitted where appropriate."""

        traverser = Mock()

        inst = RegexTest((("f.o", {"thing": "foo"}),
                          ("b.r", {"thing": "bar"})))

        eq_(inst.regex_source, r"(?P<test_0>f.o)|(?P<test_1>b.r)")

        inst.test("foo bar baz fxo", traverser)

        eq_([args[1]["thing"] for args in traverser.warning.call_args_list],
            ["foo", "bar", "foo"])
