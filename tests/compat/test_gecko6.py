from helper import CompatTestCase
from validator.compat import FX6_DEFINITION
from validator.errorbundler import ErrorBundle
from validator.testcases.markup.markuptester import MarkupParser


class TestGecko6Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 6 are properly executed."""

    VERSION = FX6_DEFINITION

    def test_window_top(self):
        """
        Test that `window.top` (a reserved global variable as of Gecko 6) is
        flagged as incompatible.
        """

        self.run_script_for_compat('window.top = "foo";');
        self.assert_silent()
        self.assert_compat_warning()

        # Also test the same script for implied global overwrites.
        self.run_script_for_compat('top = "foo";');
        self.assert_silent()
        self.assert_compat_warning()

    def test_custom_addon_types(self):
        """
        Test that registering custom add-on types is flagged as being
        incompatible with Gecko 6.
        """

        self.run_script_for_compat('AddonManagerPrivate.registerProvider();')
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_menu_item_compat(self):
        """
        Test that compatibility warnings are raised for the stuff from bug
        660349.
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

            err = test(FX6_DEFINITION)
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
