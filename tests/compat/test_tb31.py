from helper import CompatTestCase
from validator.compat import TB31_DEFINITION


class TestTB31Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 31 are properly executed."""

    VERSION = TB31_DEFINITION

    def test_nsIMsgCompose_checkAndPopulateRecipients(self):
        for method in self.run_xpcom_for_compat(
                'nsIAddrDatabase', ['addAllowRemoteContent']):
            self.assert_silent()
            self.assert_compat_error(type_='warning')

    def test_getNonHtmlRecipients(self):
        """Test that these patterns are flagged in Thunderbird 31."""
        self.run_script_for_compat('allowRemoteContentForSender()')
        self.assert_silent()
        self.assert_compat_error(type_='warning')

    def test_recentfolders_label(self):
        self.run_regex_for_compat('folderContextProperties.label')
        self.assert_silent()
        self.assert_compat_error(type_='warning')
