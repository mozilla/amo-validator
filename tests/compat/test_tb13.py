from helper import CompatTestCase
from validator.compat import TB13_DEFINITION


class TestTB13Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 13 are properly executed.
    """

    VERSION = TB13_DEFINITION

    def test_interfaces(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgLocalMailFolder", ["addMessage()"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

        for method in self.run_xpcom_for_compat(
                "nsIMsgNewsFolder", ["getGroupUsernameWithUI()"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_functions(self):
        patterns = ["serverPageInit", "loginPageInit", "serverPageValidate",
                    "serverPageUnload", "loginPageValidate", "setupBccTextbox",
                    "setupCcTextbox"]
        for pattern in patterns:
            self.run_regex_for_compat("var x = %s();" % pattern, is_js=True)
            self.assert_silent()
            assert self.compat_err.notices
            assert self.compat_err.compat_summary["errors"]

        # Extra tests for similar functions.
        for pattern in ["serverPage", "clientPageInit"]:
            self.run_regex_for_compat("var x = %s();" % pattern, is_js=True)
            self.assert_silent()
            self.assert_compat_silent()
