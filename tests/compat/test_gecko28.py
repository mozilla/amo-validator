from helper import CompatTestCase
from validator.compat import FX28_DEFINITION


class TestFX28Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 28 are properly executed."""

    VERSION = FX28_DEFINITION

    def test_js_patterns(self):
        """Test that '__SS_tabStillLoading' is flagged in Gecko 28."""
        self.run_script_for_compat(
                'var x = browser.__SS_tabStillLoading;')
        self.assert_silent()
        self.assert_compat_error()
