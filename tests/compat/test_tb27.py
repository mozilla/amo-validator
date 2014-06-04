from helper import CompatTestCase
from validator.compat import TB27_DEFINITION


class TestTB27Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 27 are properly executed."""

    VERSION = TB27_DEFINITION

    def test_startDebugger(self):
        """Test that these patterns are flagged in Thunderbird 27."""
        self.run_script_for_compat('startDebugger()')
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_string_pop3MessageFolderBusy(self):
        self.run_regex_for_compat("folderCharsetOverride.label")
        self.assert_silent()
        self.assert_compat_error(type_="warning")
