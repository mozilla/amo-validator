from helper import CompatTestCase
from validator.compat import FX41_DEFINITION


class TestFX41Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 41 are properly executed."""

    VERSION = FX41_DEFINITION

    def test_browser_newtab_url_pref(self):
        # Use `run_regex_for_compat` since this triggers warnings for changing
        # preferences.
        self.run_regex_for_compat("""
            require("sdk/preferences/service").set("browser.newtab.url", false);
        """)
        self.assert_silent()
        self.assert_compat_error()
