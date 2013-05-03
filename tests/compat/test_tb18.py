from helper import CompatTestCase
from validator.compat import TB18_DEFINITION


class TestTB18Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 18 are properly executed."""

    VERSION = TB18_DEFINITION

    def test_js_patterns(self):
        """Test that these js patterns are flagged in Thunderbird 18."""
        self.setUp()
        self.run_regex_for_compat("var x = %s();" % "queryISupportsArray")
        self.assert_compat_error(type_="notice")

    def test_prplIAccount_noNewlines(self):
        for method in self.run_xpcom_for_compat(
            "prplIAccount", ["noNewlines"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_unflagged_patterns(self):
        """Test that these js patterns are _NOT_ flagged in Thunderbird 18."""
        self.setUp()
        self.run_regex_for_compat("var x = %s();" % "IncomingServer")
        self.assert_silent()
        self.assert_compat_silent()
