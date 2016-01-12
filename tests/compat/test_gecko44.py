from helper import CompatTestCase
from validator.compat import FX44_DEFINITION


class TestFX44Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 44 are properly executed."""

    VERSION = FX44_DEFINITION

    def test_mozFetchAsStream(self):
        self.run_script_for_compat(
            'let stylesheets = window.getAllStyleSheets(config.browser.contentWindow);'
        )
        self.assert_silent()
        self.assert_compat_error()
