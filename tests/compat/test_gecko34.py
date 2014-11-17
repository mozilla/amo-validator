from helper import CompatTestCase
from validator.compat import FX34_DEFINITION


class TestFX34Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 34 are properly executed."""

    VERSION = FX34_DEFINITION

    def test_nsICommandParams(self):
        self.run_script_for_compat("""
            var cmdParams = Components.interfaces.nsICommandParams;
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")
