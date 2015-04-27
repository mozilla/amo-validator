from helper import CompatTestCase
from validator.compat import FX38_DEFINITION


class TestFX38Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 38 are properly executed."""

    VERSION = FX38_DEFINITION

    def test_mozIndexedDB(self):
        self.run_script_for_compat("""
            var db = mozIndexedDB.open('foo', 5);
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_indexedDB(self):
        self.run_script_for_compat("""
            var db = indexedDB.open('foo', 5);
        """)
        self.assert_silent()
        self.assert_compat_silent()
