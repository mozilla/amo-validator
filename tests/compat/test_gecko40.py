from helper import CompatTestCase
from validator.compat import FX40_DEFINITION


class TestFX40Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 40 are properly executed."""

    VERSION = FX40_DEFINITION

    def test_setKeywordForBookmark(self):
        self.run_script_for_compat("""
            setKeywordForBookmark(25, 'foo');
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_getKeywordForBookmark(self):
        self.run_script_for_compat("""
            getKeywordForBookmark(25);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_getURIForKeyword(self):
        self.run_script_for_compat("""
            getURIForKeyword('foo');
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")
