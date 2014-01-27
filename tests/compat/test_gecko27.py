from helper import CompatTestCase
from validator.compat import FX27_DEFINITION


class TestFX27Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 27 are properly executed."""

    VERSION = FX27_DEFINITION

    def test_js_patterns(self):
        """Test that `downloads-indicator` is flagged in Gecko 27."""
        self.run_script_for_compat(
                'var x = document.getElementById("downloads-indicator");')
        self.assert_silent()
        self.assert_compat_error()
