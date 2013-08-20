from helper import CompatTestCase
from validator.compat import TB21_DEFINITION


class TestTB21Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 21 are properly executed."""

    VERSION = TB21_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 21."""
        self.run_regex_for_compat("var x = %s();" "addEditorClickEventListener")
        self.assert_compat_error(type_="warning")

    def test_nsIMimeHeaders_initialize(self):
        for method in self.run_xpcom_for_compat(
                "nsIMimeHeaders", ["initialize"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgFolder_ListDescendants(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgFolder", ["ListDescendants"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

