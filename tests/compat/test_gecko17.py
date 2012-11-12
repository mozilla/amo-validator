from helper import CompatTestCase
from validator.compat import FX17_DEFINITION


class TestFX17Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 17 are properly executed."""

    VERSION = FX17_DEFINITION

    def test_checkLoadURI(self):
        """Test that `checkLoadURI` is flagged in Gecko 17."""
        self.run_script_for_compat("x.checkLoadURI;")
        self.assert_silent()
        self.assert_compat_error()

    def test_checkLoadURIStr(self):
        """Test that `checkLoadURIStr` is flagged in Gecko 17."""
        self.run_script_for_compat("x.checkLoadURIStr;")
        self.assert_silent()
        self.assert_compat_error()

    def test_onuploadprogress(self):
        """Test that `onuploadprogress` is flagged in Gecko 17."""
        self.run_script_for_compat("""
        var x = XMLHttpRequest();
        x.onuploadprogress = function() {};
        x.send();
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_onuploadprogress(self):
        """Test that `onuploadprogress` is flagged in Gecko 17."""
        self.run_script_for_compat("x.nsIChromeFrameMessageManager;")
        self.assert_silent()
        self.assert_compat_error()

    def test_eval_function(self):
        """Test that `eval` and `Function` are flagged in Gecko 17."""
        self.run_script_for_compat("var foo = eval('asdf');")
        self.assert_failed(with_warnings=True)
        self.assert_compat_error(type_="notice")
