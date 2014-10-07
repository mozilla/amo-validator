from helper import CompatTestCase
from validator.compat import FX31_DEFINITION


class TestFX31Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 31 are properly executed."""

    VERSION = FX31_DEFINITION

    def test_DataContainerEvent_usage(self):
        self.run_script_for_compat(
            'var e = document.createEvent("DataContainerEvent");')
        self.assert_silent()
        self.assert_compat_error()

    def test_getShortcutOrURIAndPostData_promise(self):
        self.run_script_for_compat(
            'var p = getShortcutOrURIAndPostData("something");')
        self.assert_silent()
        self.assert_compat_error()

    def test_getShortcutOrURIAndPostData_promise_yield(self):
        self.run_script_for_compat('''
            function urlAndPostData() {
                yield getShortcutOrURIAndPostData("a string");
            }
        ''')
        self.assert_silent()
        self.assert_compat_error()

    def test_getShortcutOrURIAndPostData_promise_window(self):
        self.run_script_for_compat(
            'var p = window.getShortcutOrURIAndPostData("something");')
        self.assert_silent()
        self.assert_compat_error()

    def test_getShortcutOrURIAndPostData_callback(self):
        self.run_script_for_compat(
            'getShortcutOrURIAndPostData("something", cb);')
        self.assert_silent()
        self.assert_compat_silent()

    def test_getShortcutOrURIAndPostData_callback_window(self):
        self.run_script_for_compat(
            'window.getShortcutOrURIAndPostData("something", cb);')
        self.assert_silent()
        self.assert_compat_silent()

    def test_sendAsBinary(self):
        self.run_script_for_compat('''
            var xhr = new XMLHttpRequest();
            xhr.sendAsBinary("some-data");
        ''')
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_browser_tabs_closeButtons_pref(self):
        self.run_regex_for_compat('pref("browser.tabs.closeButtons", 3)')
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsIAutoCompleteResult(self):
        self.run_script_for_compat('''
          function Result() {}
          Result.prototype = {
            QueryInterface: XPCOMUtils.generateQI([Ci.nsIAutoCompleteResult])
          };
        ''')
        self.assert_silent()
        self.assert_compat_warning(type_="warning")
