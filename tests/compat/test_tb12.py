from helper import CompatTestCase
from validator.compat import TB12_DEFINITION


class TestTB12Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 12 are properly executed.
    """

    VERSION = TB12_DEFINITION

    def test_interfaces(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgDBService", ["openMailDBFromFile()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

        for method in self.run_xpcom_for_compat(
                "nsIMsgDatabase", ["Open()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")
