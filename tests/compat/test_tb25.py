from helper import CompatTestCase
from validator.compat import TB25_DEFINITION


class TestTB25Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 25 are properly executed."""

    VERSION = TB25_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 25."""
        self.run_regex_for_compat("var x = %s();" "gSetupLdapAutocomplete")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_nsIImapMailFolderSink_progressStatus(self):
        for method in self.run_xpcom_for_compat(
                "nsIImapMailFolderSink", ["progressStatus"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_string_5093(self):
        self.run_regex_for_compat("5093")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
