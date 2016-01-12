from helper import CompatTestCase
from validator.compat import FX44_DEFINITION


class TestFX44Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 44 are properly executed."""

    VERSION = FX44_DEFINITION

    def test_new_devtools_llocation_gre(self):
        self.run_script_for_compat("""
            var devtools = Cu.import("resource://gre/modules/devtools/shared/Loader.jsm", {}).devtools;
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_new_devtools_llocation_from_root(self):
        self.run_script_for_compat("""
            var devtools = Cu.import("resource:///modules/devtools/Target.jsm", {});
        """)
        self.assert_silent()
        self.assert_compat_error()
