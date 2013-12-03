from helper import CompatTestCase
from validator.compat import FX26_DEFINITION


class TestFX26Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 26 are properly executed."""

    VERSION = FX26_DEFINITION

    def test_nsIDownloadManager(self):
        """Test that `nsIDownloadManager` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIDownloadManager(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIMemoryReporter(self):
        """Test that `nsIMemoryReporter` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIMemoryReporter(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIMemoryReporterCallback(self):
        """Test that `nsIMemoryReporterCallback` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIMemoryReporterCallback(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIMemoryReporterManager(self):
        """Test that `nsIMemoryReporterManager` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIMemoryReporterManager(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIMemoryMultiReporter(self):
        """Test that `nsIMemoryMultiReporter` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIMemoryMultiReporter(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIHistoryEntry(self):
        """Test that `nsIHistoryEntry` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIHistoryEntry(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test__firstTabs(self):
        """Test that `_firstTabs` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(_firstTabs(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_lookupMethod(self):
        """Test that `lookupMethod` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(lookupMethod(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIAccessibleProvider(self):
        """Test that `nsIAccessibleProvider` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(nsIAccessibleProvider(foo));')
        self.assert_silent()
        self.assert_compat_error()

    def test_window_history_subscript(self):
        """Test that `window.history[asdf]` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(window.history[asdf]);')
        self.assert_silent()
        self.assert_compat_error()

    def test_window_history_next(self):
        """Test that `window.history.next` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(window.history.next);')
        self.assert_silent()
        self.assert_compat_error()

    def test_window_history_current(self):
        """Test that `window.history.current` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(window.history.current);')
        self.assert_silent()
        self.assert_compat_error()

    def test_window_history_previous(self):
        """Test that `window.history.previous` is flagged in Gecko 26."""
        self.run_script_for_compat('alert(window.history.previous);')
        self.assert_silent()
        self.assert_compat_error()
