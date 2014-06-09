from helper import CompatTestCase
from validator.compat import TB29_DEFINITION


class TestTB28Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 29 are properly executed."""

    VERSION = TB29_DEFINITION

    def test_nsIMsgHeaderParser_makeMimeAddress(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgHeaderParser", ["makeMimeAddress"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_DisablePhishingWarning(self):
        """Test that these patterns are flagged in Thunderbird 29."""
        self.run_script_for_compat("DisablePhishingWarning()")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_subjectColumn_tooltip(self):
        self.run_regex_for_compat("subjectColumn.tooltip")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
