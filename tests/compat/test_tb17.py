from helper import CompatTestCase
from validator.compat import TB17_DEFINITION


class TestTB17Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 17 are properly executed.
    """

    VERSION = TB17_DEFINITION

    def test_js_patterns(self):
        """Test that these js patterns are flagged in Thunderbird 17."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern)
            self.assert_compat_error(type_="notice")

        yield test_pattern, self, "(ChangeFeedShowSummaryPref"
        yield test_pattern, self, "FeedSetContentViewToggle"
        yield test_pattern, self, "FillAttachmentListPopup"

    def test_unflagged_patterns(self):
        """Test that these js patterns are _NOT_ flagged in Thunderbird 17."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern)
            self.assert_compat_silent()

        yield test_pattern, self, "MsgonShowAttachmentListContextMenu"
        yield test_pattern, self, "ThisGetFeedOpenHandler"
