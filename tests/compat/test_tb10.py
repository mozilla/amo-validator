from helper import CompatTestCase
from validator.compat import TB10_DEFINITION


class TestTB10Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 10 are properly executed.
    """

    VERSION = TB10_DEFINITION

    def test_functions(self):
        patterns = ["MsgDeleteMessageFromMessageWindow", "goToggleSplitter",
                    "AddMessageComposeOfflineObserver",
                    "RemoveMessageComposeOfflineObserver",
                    "gDownloadManagerStrings.get"]
        for pattern in patterns:
            self.run_script_for_compat("%s();" % pattern)
            self.assert_silent()
            assert self.compat_err.warnings or self.compat_err.notices
            assert self.compat_err.compat_summary["errors"]
