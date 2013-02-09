from helper import CompatTestCase
from validator.compat import FX10_DEFINITION


class TestFX10Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 10 are properly executed."""

    VERSION = FX10_DEFINITION

    def test_isSameNode(self):
        """Test that `isSameNode` is flagged in Gecko 10."""
        self.run_script_for_compat('alert(x.isSameNode(foo));')
        self.assert_silent()
        self.assert_compat_error(type_="error")

    def test_replaceWholeText(self):
        """Test that `repalceWholeText` is flagged in Gecko 10."""
        self.run_script_for_compat('alert(x.replaceWholeText());')
        self.assert_silent()
        self.assert_compat_error(type_="error")

    def test_isElementContentWhitespace(self):
        """Test that `isElementContentWhitespace` is flagged in Gecko 10."""
        self.run_script_for_compat('alert(x.isElementContentWhitespace);')
        self.assert_silent()
        self.assert_compat_error(type_="error")

    def test_xml_docuemnt_properties(self):
        """
        Test that the `xmlEncoding`, `xmlVersion`, and `xmlStandalone` objects
        are dead for the document object in Gecko 10.
        """
        patterns = ["document.xmlEncoding", "document.xmlVersion",
                    "document.xmlStandalone", "content.document.xmlEncoding"]
        for pattern in patterns:
            self.run_script_for_compat("alert(%s);" % pattern)
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_xml_properties(self):
        """
        Test that the `xmlEncoding`, `xmlVersion`, and `xmlStandalone` objects
        are dead in Gecko 10.
        """
        patterns = ["foo.xmlEncoding", "foo.xmlVersion", "foo.xmlStandalone"]
        for pattern in patterns:
            self.run_script_for_compat("alert(%s);" % pattern)
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_interfaces(self):
        interfaces = ["nsIDOMNSHTMLFrameElement", "nsIDOMNSHTMLElement"]
        for interface in interfaces:
            self.run_script_for_compat("""
            var x = Components.classes[""].createInstance(
                        Components.interfaces.%s);
            """ % interface)
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_nsIBrowserHistory(self):
        for method in self.run_xpcom_for_compat(
                "nsIBrowserHistory", ["lastPageVisited"]):
            self.assert_silent()
            self.assert_compat_error(type_="error")
