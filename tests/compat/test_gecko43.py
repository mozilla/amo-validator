from helper import CompatTestCase
from validator.compat import FX43_DEFINITION


class TestFX43Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 38 are properly executed."""

    VERSION = FX43_DEFINITION

    def test_mozFetchAsStream(self):
        self.run_script_for_compat('canvas.mozFetchAsStream(aCallback, this.contentType);')
        self.assert_silent()
        self.assert_compat_error()
