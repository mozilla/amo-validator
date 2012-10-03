from helper import CompatTestCase
from validator.compat import FX16_DEFINITION


class TestFX16Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 16 are properly executed."""

    VERSION = FX16_DEFINITION

    def test_mozjs_incomplete(self):
        """Test that `MozWhatever*` is notflagged in Gecko 16."""
        self.run_script_for_compat("x.MozTransition;")
        self.assert_silent()
        self.assert_compat_silent()

    def test_mozjs_full(self):
        """Test that `MozWhatever*` is flagged in Gecko 16."""
        self.run_script_for_compat("x.MozTransitionStuff")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_nsitransferable(self):
        """Test that `nsITransferable` is flagged in Gecko 16."""
        self.run_script_for_compat("nsITransferable.foo.bar;")
        self.assert_silent()
        self.assert_compat_error()

    def test_mozIndexedDB(self):
        """Test that `mozIndexedDB` is flagged in Gecko 16."""
        self.run_script_for_compat("mozIndexedDB.foo.bar;")
        self.assert_silent()
        self.assert_compat_error()

    def test_java(self):
        """Test that `java` is flagged in Gecko 16."""
        self.run_script_for_compat("var x = java;")
        self.assert_silent()
        self.assert_compat_error()

    def test_Packages(self):
        """Test that `Packages` is flagged in Gecko 16."""
        self.run_script_for_compat("var x = Packages;")
        self.assert_silent()
        self.assert_compat_error()
