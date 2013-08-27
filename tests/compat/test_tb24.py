from helper import CompatTestCase
from validator.compat import TB24_DEFINITION


class TestTB24Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 24 are properly executed."""

    VERSION = TB24_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 24."""
        self.run_regex_for_compat("var x = %s();" "ArrangeAccountCentralItems")
        self.assert_compat_error(type_="warning")

    def test_nsIMsgFolder_knowsSearchNntpExtension(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgFolder", ["knowsSearchNntpExtension"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_string_overrideColors_label(self):
        self.run_regex_for_compat("folderContextOpenNewWindow.label")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
