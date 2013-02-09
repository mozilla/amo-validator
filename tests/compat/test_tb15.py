from helper import CompatTestCase
from validator.compat import TB15_DEFINITION


class TestTB15Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 15 are properly executed.
    """

    VERSION = TB15_DEFINITION

    def test_interfaces(self):
        for method in self.run_xpcom_for_compat(
                "nsIImportMail", ["ImportMailbox()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_js_patterns(self):
        """Test that these js patterns are flagged in Thunderbird 15."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern, is_js=True)
            self.assert_compat_error(type_="notice")

        for r in ["testConfigurator", ".capabilityPref", "(getFeedUrlsInFolder",
                  "debug-utils.js", "(showIMConversationInTab()", "(FZ_FEED"]:
            yield test_pattern, self, r

    def test_unflagged_patterns(self):
        """Test that these js patterns are _NOT_ flagged in Thunderbird 15."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern, is_js=True)
            self.assert_compat_silent()

        for r in ["getaddFeed", "sometimeswaitForBuddyInfo", "DC_RSS_NS",
                  "msgFeedSubscriptionsWindow", "msgetNodeValue"]:
            yield test_pattern, self, r
