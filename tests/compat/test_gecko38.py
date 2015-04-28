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

    def test_nsICompositionStringSynthesizer(self):
        self.run_script_for_compat("""
            var syn = Components.interfaces.nsICompositionStringSynthesizer;
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_sendCompositionEvent(self):
        self.run_script_for_compat("""
            var domWindowUtils = window
                .QueryInterface(Components.interfaces.nsIInterfaceRequestor)
                .getInterface(Components.interfaces.nsIDOMWindowUtils);
            domWindowUtils.sendCompositionEvent("compositionstart", "", "");
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_createCompositionStringSynthesizer(self):
        self.run_script_for_compat("""
            var domWindowUtils = window
                .QueryInterface(Components.interfaces.nsIInterfaceRequestor)
                .getInterface(Components.interfaces.nsIDOMWindowUtils);
            var compositionStringSynthesizer = domWindowUtils
                .createCompositionStringSynthesizer();
        """)
        self.assert_silent()
        self.assert_compat_error()
