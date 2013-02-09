from helper import CompatTestCase
from validator.compat import FX7_DEFINITION


class TestGecko7Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 7 are properly executed."""

    VERSION = FX7_DEFINITION

    def test_nsIDOMDocumentStyle(self):
        self.run_regex_for_compat("nsIDOMDocumentStyle")
        self.assert_silent()
        self.assert_compat_error()

    def test_nsINavHistoryObserver(self):
        self.run_regex_for_compat("nsINavHistoryObserver")
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_nsIMarkupDocumentViewer(self):
        self.run_regex_for_compat("nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsIDOMFile(self):
        """
        Test that nsIDOMFile's getAsBinary() and getAsDataURL() are flagged.
        """
        for method in self.run_xpcom_for_compat(
                "nsIDOMFile", ["getAsBinary()", "getAsDataURL()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_nsIJSON(self):
        """Test that nsIJSON's encode() and decode() methods are flagged."""
        for method in self.run_xpcom_for_compat(
                "nsIJSON", ["encode()", "decode()"]):
            self.assert_silent()
            self.assert_compat_warning()
