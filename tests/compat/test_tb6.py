from helper import CompatTestCase
from validator.compat import TB6_DEFINITION


class TestTB6Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 6 are properly executed."""

    VERSION = TB6_DEFINITION

    def test_nsIImapMailFolderSink(self):
        for method in self.run_xpcom_for_compat(
                "nsIImapMailFolderSink", ["setUrlState()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_nsIImapProtocol(self):
        for method in self.run_xpcom_for_compat(
                "nsIImapProtocol", ["NotifyHdrsToDownload()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

