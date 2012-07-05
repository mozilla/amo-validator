from helper import CompatTestCase
from validator.compat import FX14_DEFINITION


class TestFX14Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 14 are properly executed."""

    VERSION = FX14_DEFINITION

    def test_nsIPlacesImportExportService(self):
        """
        nsIPlacesImportExportService.importHTMLFromFile and .importHTMLFromURI
        have both been removed from Gecko 14.
        """
        for method in self.run_xpcom_for_compat(
                "nsIPlacesImportExportService",
                ["importHTMLFromFile", "importHTMLFromURI"]):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsIDOMHTMLDocument(self):
        """
        Test that `queryCommandText` and `execCommandShowHelp` have been
        flagged in Gecko 14.
        """
        for method in self.run_xpcom_for_compat(
                "nsIDOMHTMLDocument",
                ["queryCommandText()", "execCommandShowHelp()"]):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsINavBookmarksService(self):
        """Test that GUIDs are removed from `nsINavBookarmsService`."""

        for method in self.run_xpcom_for_compat(
                "nsINavBookmarksService", ["getItemGUID", "setItemGUID",
                                           "getItemIdForGUID"]):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsIHistoryQueryOptions(self):
        """Test that `redirectsMode` is flagged in Gecko 14."""
        for method in self.run_xpcom_for_compat(
                "nsINavHistoryQueryOptions", ["redirectsMode"]):
            self.assert_silent()
            self.assert_compat_error()

    def test_onFaviconDataAvailable(self):
        """Test that `onFaviconDataAvailable` is flagged in Gecko 14."""
        self.run_script_for_compat("alert(x.onFaviconDataAvailable());")
        self.assert_silent()
        self.assert_compat_error()

    def test_onFaviconDataAvailable_assignment(self):
        """
        Test that assignments to `onFaviconDataAvailable` is flagged in Gecko
        14.
        """
        self.run_script_for_compat("{onFaviconDataAvailable: foo()}")
        self.assert_silent()
        self.assert_compat_error()

    def test_Blob(self):
        """Test that the (Moz)BlobBuilder objects are deprecated."""
        self.run_regex_for_compat("MozBlobBuilder")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

        self.run_regex_for_compat("BlobBuilder")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsILocalFile(self):
        """
        Test that `nsILocalFile` suggests that `nsIFile` should be used
        instead.
        """
        self.run_regex_for_compat("nsILocalFile")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

