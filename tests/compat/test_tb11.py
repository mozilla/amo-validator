from helper import CompatTestCase
from validator.compat import TB11_DEFINITION


class TestTB11Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 11 are properly executed.
    """

    VERSION = TB11_DEFINITION

    def test_interfaces(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgQuote", ["quoteMessage()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

        for method in self.run_xpcom_for_compat(
                "nsIMailtoUrl", ["GetMessageContents()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

