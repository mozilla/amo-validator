from helper import CompatTestCase
from validator.compat import FX37_DEFINITION


class TestFX37Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 37 are properly executed."""

    VERSION = FX37_DEFINITION

    def test_string_quote_variable(self):
        self.run_script_for_compat("""
            var myString = "A string!";
            console.log(myString.quote());
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_string_quote_argument(self):
        self.run_script_for_compat("""
            function printString(myString) {
                console.log(myString.quote());
            }
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_string_quote_literal(self):
        self.run_script_for_compat("""
            console.log("A string!".quote());
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_nsIDownloadManagerUI(self):
        self.run_script_for_compat("""
            var downloads = Cc["@mozilla.org/download-manager-ui;1"]
                .getService(Ci.nsIDownloadManagerUI);
        """)
        self.assert_silent()
        self.assert_compat_error()
