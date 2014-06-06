from helper import CompatTestCase
from validator.compat import TB28_DEFINITION


class TestTB28Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 28 are properly executed."""

    VERSION = TB28_DEFINITION

    def test_nsMsgFolderFlags_subscribed(self):
        for method in self.run_xpcom_for_compat(
                "nsMsgFolderFlags", ["ImapServer"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_onRecipientsInput(self):
        """Test that these patterns are flagged in Thunderbird 28."""
        self.run_script_for_compat("onRecipientsInput()")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def mdnBarSendButton2_label(self):
        self.run_regex_for_compat("mdnBarSendButton2.accesskey")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
