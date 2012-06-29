from helper import CompatTestCase
from validator.compat import FX13_DEFINITION


class TestFX13Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 13 are properly executed."""

    VERSION = FX13_DEFINITION

    def test_startendMarker(self):
        """Test that _startMarker and _endMarker are flagged in Gecko 13."""

        patterns = ["bar()._startMarker",
                    "bar()._startMarker = 1",
                    "bar()._endMarker",
                    "bar()._endMarker = 1"]
        for pattern in patterns:
            self.run_script_for_compat(pattern)
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_excludeItemsIfParentHasAnnotation(self):
        """
        Test that `excludeItemsIfParentHasAnnotation` is flagged in Gecko 13.
        """
        self.run_regex_for_compat("excludeItemsIfParentHasAnnotation")
        self.assert_silent()
        self.assert_compat_error()

    def test_globalStorage_flagged(self):
        """Test that `globalStorage` is flagged in Gecko 13."""
        self.run_regex_for_compat('globalStorage["foo"]')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsILivemarkService(self):
        self.run_regex_for_compat("nsILivemarkService")
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIPrefBranch2(self):
        self.run_regex_for_compat("nsIPrefBranch2")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsIScriptableUnescapeHTML(self):
        self.run_regex_for_compat("nsIScriptableUnescapeHTML")
        self.assert_silent()
        self.assert_compat_warning()

    def test_nsIAccessNode(self):
        self.run_regex_for_compat("nsIAccessNode")
        self.assert_silent()
        self.assert_compat_error()

