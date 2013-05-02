from helper import CompatTestCase
from validator.compat import TB19_DEFINITION


class TestTB19Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 19 are properly executed."""

    VERSION = TB19_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 19."""
        self.setUp()
        self.run_regex_for_compat("var x = %s();" "enableEditableFields")
        self.assert_compat_error(type_="notice")

    def test_nsIMsgCompFields_newshost(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgCompFields", ["newshost"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgSearchAdapter_CurrentUrlDone(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgSearchAdapter", ["CurrentUrlDone"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

