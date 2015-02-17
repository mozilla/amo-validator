from helper import CompatTestCase
from validator.compat import FX36_DEFINITION


class TestFX36Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 36 are properly executed."""

    VERSION = FX36_DEFINITION

    def nsIBoxObject_changed(self, interface):
        self.run_script_for_compat("""
            var obj = Components.interfaces.{interface};
        """.format(interface=interface))
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIBoxObject')

    def test_nsIBrowserBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIBrowserBoxObject')

    def test_nsIContainerBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIContainerBoxObject')

    def test_nsIEditorBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIEditorBoxObject')

    def test_nsIIFrameBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIIFrameBoxObject')

    def test_nsIListBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIListBoxObject')

    def test_nsIMenuBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIMenuBoxObject')

    def test_nsIPopupBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIPopupBoxObject')

    def test_nsIScrollBoxObject_changed(self):
        self.nsIBoxObject_changed('nsIScrollBoxObject')

    def test_nsITreeBoxObject_changed(self):
        self.nsIBoxObject_changed('nsITreeBoxObject')

    def test_nsIFoo_BoxObject_no_error(self):
        self.run_script_for_compat("""
            var nsIFoo = myBoxObject;
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_at_at_iterator(self):
        self.run_script_for_compat("""
            var iterator = something['@@iterator'];
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_OS_File_readTo(self):
        self.run_script_for_compat("""
            function yieldMustBeInAFunction() {
                let f = yield OS.File.open('path/to/file.txt', {read: true});
                let numBytes;
                let array = new Uint8Array(0x8000);
                numBytes = yield f.readTo(array);
            }
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_global_readTo(self):
        self.run_script_for_compat("""
            var something = readTo("something to read into, or something");
        """)
        self.assert_silent()
        self.assert_compat_silent()
