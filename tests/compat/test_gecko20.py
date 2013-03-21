from helper import CompatTestCase
from validator.compat import FX20_DEFINITION


class TestFX20Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 20 are properly executed."""

    VERSION = FX20_DEFINITION

    def test_private_browsing(self):
        self.run_script_for_compat("""
            var y = "private-browsing";
        """)
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_global_private_browsing_service(self):
        self.run_script_for_compat("""
            var x = nsIPrivateBrowsingService;
        """)
        self.assert_silent()
        self.assert_compat_error(type_="notice")
