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

    def test_asyncFetch2(self):
        self.run_script_for_compat("""
            NetUtil.asyncFetch2(
                NetUtil.newURI(download.source.url),
                null,
                null,
                null,      // aLoadingNode
                Services.scriptSecurityManager.getSystemPrincipal(),
                null,      // aTriggeringPrincipal
                Ci.nsILoadInfo.SEC_NORMAL,
                Ci.nsIContentPolicy.TYPE_OTHER);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_asyncFetch(self):
        self.run_script_for_compat("""
            NetUtil.asyncFetch({
                uri: "http://localhost:5555/test",
                loadUsingSystemPrincipal: true,
            });
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_newChannel2(self):
        self.run_script_for_compat("""
            NetUtil.newChannel2(
                NetUtil.newURI(download.source.url),
                null,
                null,
                null,      // aLoadingNode
                Services.scriptSecurityManager.getSystemPrincipal(),
                null,      // aTriggeringPrincipal
                Ci.nsILoadInfo.SEC_NORMAL,
                Ci.nsIContentPolicy.TYPE_OTHER);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_newChannel(self):
        self.run_script_for_compat("""
            NetUtil.newChannel({
                uri: "data:text/plain,",
                loadUsingSystemPrincipal: true,
            });
        """)
        self.assert_silent()
        self.assert_compat_silent()

    def test_onProxyAvailable(self):
        self.run_script_for_compat("""
            onProxyAvailable(nsIChannel);
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_asyncResolve(self):
        self.run_script_for_compat("""
            asyncResolve(nsIChannel);
        """)
        self.assert_silent()
        self.assert_compat_error()
