from helper import CompatTestCase
from validator.compat import FX12_DEFINITION


class TestFX12Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 12 are properly executed."""

    VERSION = FX12_DEFINITION

    def test_chromemargin(self):
        self.run_regex_for_compat('<foo chromemargin="1">')
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_documentCharsetInfo(self):
        self.run_regex_for_compat('window.documentCharsetInfo;')
        self.assert_silent()
        self.assert_compat_error()

    def test_interfaces(self):
        interfaces = ["nsIJetpack", "nsIJetpackService",
                      "nsIProxyObjectManager"]
        for interface in interfaces:
            self.run_regex_for_compat("Components.interfaces.%s" % interface)
            self.assert_silent()
            self.assert_compat_error()

