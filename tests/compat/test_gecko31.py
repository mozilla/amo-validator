from helper import CompatTestCase
from validator.compat import FX31_DEFINITION


class TestFX31Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 30 are properly executed."""

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
