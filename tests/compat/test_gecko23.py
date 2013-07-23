from helper import CompatTestCase
from validator.compat import FX23_DEFINITION


class TestFX23Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 23 are properly executed."""

    VERSION = FX23_DEFINITION

    def test_usfuc(self):
        self.run_regex_for_compat("URI_SAFE_FOR_UNTRUSTED_CONTENT", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_faildocumentload_no_quotes(self):
        self.run_regex_for_compat('FailDocumentLoad', is_js=True)
        self.assert_silent()
        self.assert_compat_silent()

    def test_faildocumentload(self):
        self.run_regex_for_compat('"FailDocumentLoad"', is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")
