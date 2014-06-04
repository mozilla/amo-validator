from helper import CompatTestCase
from validator.compat import TB26_DEFINITION


class TestTB26Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 26 are properly executed."""

    VERSION = TB26_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 26."""
        self.run_regex_for_compat(
            '<script type="application/x-javascript" '
            'src="chrome://messenger/content/widgetglue.js"/>')
        self.assert_silent()        
        self.assert_compat_error(type_="warning")

    def test_onAbSearchReset(self):
        self.run_script_for_compat("onAbSearchReset()")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_string_pop3MessageFolderBusy(self):
        self.run_regex_for_compat("pop3MessageFolderBusy")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
