from helper import CompatTestCase
from validator.compat import FX11_DEFINITION


class TestFX11Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 11 are properly executed."""

    VERSION = FX11_DEFINITION

    def test_requestAnimationFrame(self):
        """Test that requestAnimationFrame requires at least one parameter."""

        self.run_script_for_compat('requestAnimationFrame(foo);')
        self.assert_silent()
        self.assert_compat_silent()

        self.run_script_for_compat('requestAnimationFrame();')
        self.assert_silent()
        self.assert_compat_error()

    def test_patterns(self):
        patterns = ["nsICharsetResolver", '"omni.jar"']
        for pattern in patterns:
            self.run_regex_for_compat(pattern)
            self.assert_silent()
            self.assert_compat_error()

