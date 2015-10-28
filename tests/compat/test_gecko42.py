from helper import CompatTestCase
from validator.compat import FX42_DEFINITION


class TestFX42Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 42 are properly executed."""

    VERSION = FX42_DEFINITION

    def test_parseContentType(self):
        self.run_script_for_compat("""
            var netutil = Components
              .classes["@mozilla.org/network/util;1"]
              .getService(Components.interfaces.nsINetUtil);
            netutil.parseContentType('text/html', 'utf-8', {});
        """)
        self.assert_compat_error()
