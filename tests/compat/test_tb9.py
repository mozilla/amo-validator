from helper import CompatTestCase
from validator.compat import TB9_DEFINITION


class TestTB9Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 9 are properly executed."""

    VERSION = TB9_DEFINITION

    def test_functions(self):
        patterns = ["gComposeBundle", "FocusOnFirstAttachment",
                    "WhichPaneHasFocus"]
        for pattern in patterns:
            self.run_script_for_compat("%s();" % pattern)
            self.assert_silent()
            self.assert_compat_error(type_="notice")
