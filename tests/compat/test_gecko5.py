from helper import CompatTestCase
from validator.compat import FX5_DEFINITION


class TestFX5Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 5 are properly executed."""

    VERSION = FX5_DEFINITION

    def test_navigator_language(self):
        """
        Test that `navigator.language is flagged as potentially incompatible
        with Gecko 5.
        """

        self.run_script_for_compat('alert(navigator.language);')
        self.assert_silent()

        self.assert_compat_error(type_="notice")

