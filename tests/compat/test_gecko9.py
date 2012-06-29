from helper import CompatTestCase
from validator.compat import FX9_DEFINITION


class TestGecko9Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 9 are properly executed."""

    VERSION = FX9_DEFINITION

    def test_taintEnabled(self):
        self.run_script_for_compat("alert(navigator.taintEnabled);")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_documentURIObject(self):
        self.run_script_for_compat("alert(document.documentURIObject);")
        self.assert_silent()
        self.assert_compat_warning()

    def test_nodePrincipal(self):
        self.run_script_for_compat("alert(document.nodePrincipal);")
        self.assert_silent()
        self.assert_compat_warning()

    def test_baseURIObject(self):
        self.run_script_for_compat("alert(document.baseURIObject);")
        self.assert_silent()
        self.assert_compat_warning()

    def test_nsIGlobalHistory3(self):
        self.run_regex_for_compat("nsIGlobalHistory3")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsIURLParser_parsePath(self):
        """nsIURLParser.parsePath takes 8 args instead of 10 now."""

        self.run_script_for_compat("""
        var URLi = Components.classes[
                        "@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, paramPos = {}, paramLen = {},
            queryPos = {}, queryLen = {}, refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, paramPos,
                       paramLen, queryPos, queryLen, refPos, refLen);
        """)
        self.assert_silent()
        self.assert_compat_error(type_="error")

        self.run_script_for_compat("""
        var URLi = Components.classes[
                        "@mozilla.org/network/url-parser;1?auth=maybe"].
                       createInstance(Components.interfaces.nsIURLParser);
        var filepathPos = {}, filepathLen = {}, queryPos = {}, queryLen = {},
            refPos = {}, refLen = {};
        URLi.parsePath(urlObj.path, -1, filepathPos, filepathLen, queryPos,
                       queryLen, refPos, refLen);
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_nsIURL(self):
        """nsIURL.param was removed in Gecko 9."""
        for method in self.run_xpcom_for_compat("nsIURL", ["param"]):
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_nsIBrowserHistory_removePages(self):
        """
        nsIBrowserHistory.removePages() takes 2 arguments instead of 3 in Gecko
        9.
        """

        self.run_script_for_compat("""
        var history = Components.classes[""].getService(
                        Components.interfaces.nsIBrowserHistory);
        history.removePages(foo, bar, false);
        """)
        self.assert_silent()
        self.assert_compat_error(type_="error")

        self.run_script_for_compat("""
        var history = Components.classes[""].getService(
                        Components.interfaces.nsIBrowserHistory);
        history.removePages(foo, bar);
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_nsIBrowserHistory_register(self):
        """
        nsIBrowserHistory.registerOpenPage() and
        nsIBrowserHistory.unregisterOpenPage() no longer exist in Gecko 9.
        """

        for method in self.run_xpcom_for_compat(
                "nsIBrowserHistory", ["registerOpenPage()",
                                      "unregisterOpenPage()"]):
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_nsIEditorSpellCheck_saveDefaultDictionary(self):
        """
        In Gecko 9, nsIEditorSpellCheck no longer has the function
        `saveDefaultDictionary()`.
        """
        for method in self.run_xpcom_for_compat(
                "nsIEditorSpellCheck", ["saveDefaultDictionary"]):
            self.assert_silent()
            self.assert_compat_error(type_="error")

    def test_nsIEditorSpellCheck_UpdateCurrentDictionary(self):
        """
        In Gecko 9, nsIEditorSpellCheck.UpdateCurrentDictionary no longer
        accepts parameters.
        """

        self.run_script_for_compat("""
        var editor = Components.classes[""].getService(
                        Components.interfaces.nsIEditorSpellCheck);
        editor.UpdateCurrentDictionary(foo, bar);
        """)
        self.assert_silent()
        self.assert_compat_error(type_="error")

        self.run_script_for_compat("""
        var editor = Components.classes[""].getService(
                        Components.interfaces.nsIEditorSpellCheck);
        editor.UpdateCurrentDictionary();
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_geo_prefs(self):
        """
        `geo.wifi.uri` and `geo.wifi.protocol` are no longer set in Gecko 9.
        Referring to them produces a compatibility error.
        """

        self.run_script_for_compat("""
        var app = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
        var _uri = app.prefs.get('geo.wifi.uri');
        """)
        self.assert_silent()
        self.assert_compat_error()

        self.run_script_for_compat("""
        var app = Components.classes["@mozilla.org/fuel/application;1"]
                      .getService(Components.interfaces.fuelIApplication);
        var _protocol = app.prefs.get('geo.wifi.protocol');
        """)
        self.assert_silent()
        self.assert_compat_error()

