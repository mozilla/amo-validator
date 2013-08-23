from helper import CompatTestCase
from validator.compat import TB23_DEFINITION


class TestTB23Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 23 are properly executed."""

    VERSION = TB23_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 23."""
        self.run_regex_for_compat("var x = %s();" "FinishHTMLSource")
        self.assert_compat_error(type_="warning")

    def test_string_openWindowWarningText(self):
        self.run_regex_for_compat("openWindowWarningText")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
