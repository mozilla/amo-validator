from helper import CompatTestCase
from validator.compat import FX15_DEFINITION


class TestFX15Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 15 are properly executed."""

    VERSION = FX15_DEFINITION

    def test_addPageWithDetails(self):
        """Test that `addPageWithDetails` is flagged in Gecko 15."""
        self.run_script_for_compat("alert(x.addPageWithDetails());")
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIGlobalHistory(self):
        """Test that `nsIGlobalHistory` is flagged in Gecko 15."""
        self.run_regex_for_compat("nsIGlobalHistory")
        self.assert_silent()
        self.assert_compat_error()

    def test_mozIStorageStatementWrapper(self):
        """Test that `mozIStorageStatementWrapper` is flagged in Gecko 15."""
        self.run_regex_for_compat("mozIStorageStatementWrapper")
        self.assert_silent()
        self.assert_compat_error()

    def test_private_properties(self):
        """
        Test that the private properties that were removed from Places code
        are flagged in Gecko 15.
        """
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat(pattern)
            self.assert_silent()
            self.assert_compat_error()

        for r in ["_DOMElement", "_feedURI", "_siteURI", "_cellProperties"]:
            yield test_pattern, self, r

    def test_warn_e4x(self):
        """Test that E4X is flagged as a warning properly."""
        self.run_script_for_compat("""
        var x = <foo></foo>;
        """)
        self.assert_failed(with_warnings=True)
        self.assert_compat_warning("warning")
