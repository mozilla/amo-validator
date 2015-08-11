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
        self.assert_compat_warning(type_='warning')

    def test_getKeywordForBookmark(self):
        self.run_script_for_compat("""
            getKeywordForBookmark(25);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_getURIForKeyword(self):
        self.run_script_for_compat("""
            getURIForKeyword('foo');
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_fuelIApplication(self):
        self.run_script_for_compat("""
            var Application = Components
                .classes["@mozilla.org/fuel/application;1"]
                .getService(Components.interfaces.fuelIApplication);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_extIApplication(self):
        self.run_script_for_compat("""
            var Application = Components
                .classes["@mozilla.org/fuel/application;1"]
                .getService(Components.interfaces.extIApplication);
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_Application(self):
        self.run_script_for_compat("""
            Application.restart();
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_Dict_jsm(self):
        self.run_script_for_compat("""
            Components.utils.import("resource://gre/modules/Dict.jsm");
            var newDict = new Dict();
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_sessionstore_state_write_observer(self):
        self.run_script_for_compat("""
            let observer = {
                observe: function(subject, topic, data) {
                    if (topic === 'sessionstore-state-write') {
                        alert('this will not work anymore');
                    }
                }
            };
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_nsISSLErrorListener_observer(self):
        self.run_script_for_compat("""
            // I don't know how this is used...
            'nsISSLErrorListener';
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_sdk_widget_double(self):
        self.run_script_for_compat("""
            require("sdk/widget").Widget({
                id: "mozilla-icon",
                label: "My Mozilla Widget",
                contentURL: "http://www.mozilla.org/favicon.ico"
            });
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_sdk_widget_single(self):
        self.run_script_for_compat("""
            require('sdk/widget').Widget({
                id: "mozilla-icon",
                label: "My Mozilla Widget",
                contentURL: "http://www.mozilla.org/favicon.ico"
            });
        """)
        self.assert_silent()
        self.assert_compat_error()
