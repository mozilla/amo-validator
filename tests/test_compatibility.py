import validator.constants
import validator.testcases.compatibility as compatibility
from validator.decorator import versions_after
from validator.testcases.markup.markuptester import MarkupParser
import validator.testcases.scripting as scripting
from validator.decorator import versions_after
from js_helper import _do_real_test_raw
from validator.errorbundler import ErrorBundle


def test_versions_after():
    """
    Tests that the appropriate versions after the specified versions are
    returned.
    """

    av = validator.constants.APPROVED_APPLICATIONS

    new_versions = {"1": {"guid": "foo",
                          "versions": map(str, range(10))}}
    validator.constants.APPROVED_APPLICATIONS = new_versions

    assert compatibility.versions_after("foo", "8") == ["8", "9"]
    assert compatibility.versions_after("foo", "5") == ["5", "6", "7", "8",
                                                        "9"]

    validator.constants.APPROVED_APPLICATIONS = av


def test_navigator_language():
    """
    Test that 'navigator.language' is flagged as potentially incompatile with FX5.
    """

    err = ErrorBundle()

    flagged = "alert(navigator.language);"
    scripting.test_js_snippet(err, flagged, "foo")
    assert not err.failed()

    print err.print_summary()
    print err.get_resource("compat_references")

    compatibility.navigator_language(err, None)
    assert err.failed()
    assert err.warnings[0]["compatibility_type"] == "error"


def test_menu_item_compat():
    """
    Test that compatibility warnings are raised for the stuff from bug 660349.
    """

    def _run_test(data, name="foo.xul", should_fail=False):
        def test(versions):
            err = ErrorBundle()
            err.supported_versions = versions
            parser = MarkupParser(err)
            parser.process(name,
                           data,
                           name.split(".")[-1])
            print err.print_summary(verbose=True)
            assert not err.failed()
            return err

        err = test({"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                        versions_after("firefox", "6.0a1")})
        if should_fail:
            assert err.notices
            assert err.compat_summary["warnings"]
        else:
            assert not err.notices

        assert not test({}).notices

    # Test that the testcase doesn't apply to non-XUL files.
    err = _run_test("""
    <foo>
        <bar insertbefore="webConsole" />
    </foo>
    """, name="foo.xml")

    # Test that a legitimate testcase will fail.
    err = _run_test("""
    <foo>
        <bar insertbefore="what,webConsole,evar" />
    </foo>
    """, should_fail=True)

    # Test that the testcase only applies to the proper attribute values.
    err = _run_test("""
    <foo>
        <bar insertbefore="something else" />
    </foo>
    """)


def test_window_top():
    """
    Test that 'window.top' (a reserved global variable as of Firefox 6) is
    flagged as incompatible.
    """

    err = _do_real_test_raw("""
    window.top = "foo";
    top = "bar";
    """)
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    window.top = "foo";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       versions_after("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]

    err = _do_real_test_raw("""
    top = "foo";
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       versions_after("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["warnings"]


def test_custom_addon_types():
    """
    Test that registering custom add-on types is flagged as being incompatible
    with Firefox 6.
    """

    err = _do_real_test_raw("""
    AddonManagerPrivate.registerProvider();
    """)
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert not err.notices

    err = _do_real_test_raw("""
    AddonManagerPrivate.registerProvider();
    """, versions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                       versions_after("firefox", "6.0a1")})
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert err.notices
    assert err.compat_summary["errors"]

