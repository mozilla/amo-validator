from helper import CompatTestCase
from validator.compat import TB22_DEFINITION


class TestTB22Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 22 are properly executed."""

    VERSION = TB22_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 22."""
        self.run_regex_for_compat("var x = %s();" "InitAppEditMessagesMenu")
        self.assert_compat_error(type_="warning")

    def test_nsISmtpService_deleteSmtpServer(self):
        for method in self.run_xpcom_for_compat(
                "nsISmtpService", ["deleteSmtpServer"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_string_overrideColors_label(self):
        self.run_regex_for_compat("overrideColors.label")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_string_openFeedWebPageInWindow_accesskey(self):
        self.run_regex_for_compat("openFeedWebPageInWindow.accesskey")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

