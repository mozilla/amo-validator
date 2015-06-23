from nose.tools import eq_

from .js_helper import TestCase, _do_test_raw

from validator.testcases.javascript.jstypes import JSWrapper
from validator.testcases.javascript.actions import _get_as_num


def test_array_destructuring():
    """
    Make sure that multi-level and prototype array destructuring don't cause
    tracebacks.
    """
    assert not _do_test_raw("""
    [a, b, c, d] = [1, 2, 3, 4];
    [] = bar();
    """).failed()

    assert not _do_test_raw("""
    function foo(x, y, [a, b, c], z) {
        bar();
    }
    """).failed()


def test_get_as_num():
    """Test that _get_as_num performs as expected."""

    def test(input, output):
        eq_(_get_as_num(input), output)

    yield test, 1, 1
    yield test, 1.0, 1.0
    yield test, "1", 1
    yield test, "1.0", 1.0
    yield test, None, 0
    yield test, "0xF", 15
    yield test, True, 1
    yield test, False, 0

    yield test, JSWrapper(3), 3
    yield test, JSWrapper(None), 0


def test_spidermonkey_warning():
    """
    Test that stderr warnings in Spidermonkey do not trip runtime errors.
    """
    # The following is attempting to store the octal "999999999999" in x, but
    # this is an invalid octal obviously. We need to "use strict" here because
    # the latest versions of spidermonkey simply accept that as a base 10
    # number, despite the "0" prefix.
    # We need spidermonkey to choke on this code, and this test makes sure that
    # when spidermonkey does, it doesn't break the validator.
    assert _do_test_raw("""
    "use strict";
    var x = 0999999999999;
    """).failed()


def test_blocks_evaluated():
    """
    Tests that blocks of code are actually evaluated under normal
    circumstances.
    """

    ID = ("javascript", "dangerous_global", "eval")

    EVIL = "eval(evilStuff)"
    BLOCKS = (
        "function foo() { %s; }",
        "function foo() { %s; yield 1; }",
        "function foo() { yield %s; }",
        "var foo = function () { %s; }",
        "var foo = function () { %s; yield 1; }",
        "function* foo() { %s; }",
        "var foo = function* () { %s; }",
        "var foo = function () %s",
        "var foo = () => %s",
        "var foo = () => { %s }",
        "if (true) { %s }",
        "if (true) ; else { %s }",
        "while (true) { %s }",
        "do { %s } while (true)",
        "for (;;) { %s }",
        "try { %s } catch (e) {}",
        "try {} catch (e) { %s }",
        "try {} finally { %s }",
        "try {} catch (e if %s) {}",
    )

    for block in BLOCKS:
        err = _do_test_raw(block % EVIL)
        eq_(err.message_count, 1)
        eq_(err.warnings[0]["id"], ID)


class TestTemplateString(TestCase):
    WARNING = {"id": ("testcases_chromemanifest", "test_resourcemodules",
                      "resource_modules")}

    def test_template_string(self):
        """Tests that plain template strings trigger warnings like normal
        strings."""

        self.run_script("`JavaScript-global-property`")
        self.assert_failed(with_warnings=[self.WARNING])

    def test_template_complex_string(self):
        """Tests that complex template strings trigger warnings like normal
        strings."""

        self.run_script("`JavaS${'cript-'}glob${'al-pro'}perty`")
        self.assert_failed(with_warnings=[self.WARNING])

    def test_tagged_template_string(self):
        """Tests that tagged template strings are treated as calls."""

        warning = {"id": ("testcases_javascript_instanceactions",
                          "_call_expression", "called_createelement")}

        assert not _do_test_raw("""
            d.createElement(); "script";
            d.createElement; "script";
        """).failed()

        self.run_script("""
            d.createElement`script`
        """)
        self.assert_failed(with_warnings=[warning])
