from helper import CompatTestCase
from validator.compat import FX18_DEFINITION


class TestFX18Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 18 are properly executed."""

    VERSION = FX18_DEFINITION

    def test_proxy(self):
        """Test that the proxy interfaces are properly flagged."""
        for interface in ["nsIProtocolProxyService", "nsIProxyAutoConfig",
                          "newProxiedChannel"]:
            self.compat_err = None
            self.setup_err()
            self.run_script_for_compat("foo.%s" % interface)
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_download(self):
        """Test that the downloads functions are properly flagged."""
        for interface in ["addDownload", "saveURL"]:
            self.compat_err = None
            self.setup_err()
            self.run_script_for_compat("foo.%s" % interface)
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_saveURI(self):
        """Test that `saveURI` is flagged in Gecko 18."""
        self.run_script_for_compat("x.saveURI();")
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_imgitools(self):
        """Test that the imgI<foo> interfaces are properly flagged."""
        for interface in ["imgICache", "imgILoader", "imgIToolsx"]:
            self.compat_err = None
            self.setup_err()
            self.run_script_for_compat("foo.%s" % interface)

            self.assert_silent()
            if interface != "imgIToolsx":
                self.assert_compat_error(type_="warning")
            else:
                self.assert_compat_silent()

    def test_removeDataFromDomain(self):
        """Test that `removeDataFromDomain` is flagged in Gecko 18."""
        self.run_script_for_compat("x.removeDataFromDomain();")
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_openCacheEntry(self):
        """Test that `openCacheEntry` is flagged in Gecko 18."""
        self.run_script_for_compat("x.openCacheEntry();")
        self.assert_silent()
        self.assert_compat_error(type_="notice")

    def test_BlobBuilder(self):
        """Test that `BlobBuilder` is flagged in Gecko 18."""
        self.run_script_for_compat("var x = new BlobBuilder();")
        self.assert_silent()
        self.assert_compat_error()

    def test_setAndLoadFaviconForPage(self):
        """Test that `setAndLoadFaviconForPage` is flagged in Gecko 18."""
        self.run_script_for_compat("x.setAndLoadFaviconForPage();")
        self.assert_silent()
        self.assert_compat_error(type_="notice")
