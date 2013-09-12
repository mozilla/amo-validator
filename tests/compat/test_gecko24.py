from helper import CompatTestCase
from validator.compat import FX24_DEFINITION


class TestFX24Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 24 are properly executed."""

    VERSION = FX24_DEFINITION

    def test_verifyForUsage(self):
        """Test that `verifyForUsage` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(x.verifyForUsage(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_preventBubble(self):
        """Test that `preventBubble` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.preventBubble(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_preventCapture(self):
        """Test that `preventCapture` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.preventCapture(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIDocShellHistory(self):
        """Test that `nsIDocShellHistory` is flagged in Gecko 24."""
        self.run_script_for_compat('nsIDocShellHistory.foo.bar();')
        self.assert_silent()
        self.assert_compat_error()

    def test_routeEvent(self):
        """Test that `routeEvent` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.routeEvent(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_enableExternalCapture(self):
        """Test that `enableExternalCapture` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.enableExternalCapture(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_disableExternalCapture(self):
        """Test that `disableExternalCapture` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.disableExternalCapture(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_getPreventDefault(self):
        """Test that `getPreventDefault` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.getPreventDefault(foo));')
        self.assert_silent()
        self.assert_compat_warning()

    def test_nsIFormHistory2(self):
        """Test that `nsIFormHistory2` is flagged in Gecko 24."""
        self.run_script_for_compat('alert(e.nsIFormHistory2(foo));')
        self.assert_silent()
        self.assert_compat_warning()
