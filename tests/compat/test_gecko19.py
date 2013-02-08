from helper import CompatTestCase
from validator.compat import FX19_DEFINITION


class TestFX19Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 19 are properly executed."""

    VERSION = FX19_DEFINITION

    def test_nsIConsoleService_GetMessageArray(self):
        for method in self.run_xpcom_for_compat(
            "nsIConsoleService", ["getMessageArray()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_nsIContentPrefService(self):
        self.run_regex_for_compat("nsIContentPrefService", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="notice")
