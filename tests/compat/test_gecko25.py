from helper import CompatTestCase
from validator.compat import FX25_DEFINITION


class TestFX25Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 25 are properly executed."""

    VERSION = FX25_DEFINITION

    def test_getShortcutOrURI(self):
        """Test that `getShortcutOrURI` is flagged in Gecko 25."""
        self.run_script_for_compat('alert(x.getShortcutOrURI(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test__canonizeURL(self):
        """Test that `_canonizeURL` is flagged in Gecko 25."""
        self.run_script_for_compat('alert(e._canonizeURL(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_findbarxml(self):
        """Test that `findbar.xml` is flagged in Gecko 25."""
        self.run_script_for_compat('alert(e.test("findbar.xml"));')
        self.assert_silent()
        self.assert_compat_error()

    def test_getAnnotationURI(self):
        """Test that `getAnnotationURI` is flagged in Gecko 25."""
        self.run_script_for_compat('getAnnotationURI.foo.bar();')
        self.assert_silent()
        self.assert_compat_error()

    def test_getPageAnnotationBinary(self):
        """Test that `getPageAnnotationBinary` is flagged in Gecko 25."""
        self.run_script_for_compat('getPageAnnotationBinary.foo.bar();')
        self.assert_silent()
        self.assert_compat_error()
