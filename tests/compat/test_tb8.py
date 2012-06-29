from helper import CompatTestCase
from validator.compat import TB8_DEFINITION


class TestTB8Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 8 are properly executed."""

    VERSION = TB8_DEFINITION

    def test_nsIMsgSearchScopeTerm(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgSearchScopeTerm", ["mailFile()", "inputStream()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

