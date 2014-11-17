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

    def test_rdf_local_store(self):
        self.run_script_for_compat("""
            var something = iDunno["rdf:local-store"];
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_PlacesUIUtils_localStore(self):
        self.run_script_for_compat("""
            var it = PlacesUIUtils.localStore["key"];
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_GreD(self):
        self.run_script_for_compat("""
            var it = getFile('GreD/some-file.json');
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsIMarkupDocumentViewer(self):
        self.run_script_for_compat("""
            var markupDV = Components.interfaces.nsIMarkupDocumentViewer;
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_setCharsetForURI(self):
        self.run_script_for_compat("""
            history.setCharsetForURI('foo', 'bar');
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_getCharsetForURI(self):
        self.run_script_for_compat("""
            var charset = history.getCharsetForURI('foo');
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_createStorage(self):
        self.run_script_for_compat("""
            var storage = Services.domStorageManager.createStorage();
        """)
        self.assert_silent()
        self.assert_compat_error(type_="warning")
