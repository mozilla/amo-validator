from helper import CompatTestCase
from validator.compat import FX8_DEFINITION


class TestGecko8Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 8 are properly executed."""

    VERSION = FX8_DEFINITION

    def test_nsISelection2(self):
        self.run_regex_for_compat("nsISelection2")
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIDOMWindowInternal(self):
        self.run_regex_for_compat("nsIDOMWindowInternal")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_ISO8601DateUtils(self):
        self.run_regex_for_compat("ISO8601DateUtils")
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_getSelection(self):
        self.run_script_for_compat("document.getSelection();")
        self.assert_silent()
        self.assert_compat_error(type_="notice")
