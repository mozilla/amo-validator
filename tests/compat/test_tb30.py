from helper import CompatTestCase
from validator.compat import TB30_DEFINITION


class TestTB30Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 30 are properly executed."""

    VERSION = TB30_DEFINITION

    def test_nsIMsgCompose_checkAndPopulateRecipients(self):
        for method in self.run_xpcom_for_compat(
                'nsIMsgCompose', ['checkAndPopulateRecipients']):
            self.assert_silent()
            self.assert_compat_error(type_='warning')

    def test_getNonHtmlRecipients(self):
        """Test that these patterns are flagged in Thunderbird 30."""
        self.run_script_for_compat('getNonHtmlRecipients()')
        self.assert_silent()
        self.assert_compat_error(type_='warning')

    def test_recentfolders_label(self):
        self.run_regex_for_compat('recentfolders.label')
        self.assert_silent()
        self.assert_compat_error(type_='warning')
