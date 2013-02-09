from helper import CompatTestCase
from validator.compat import TB14_DEFINITION


class TestTB14Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 14 are properly executed.
    """

    VERSION = TB14_DEFINITION

    def test_interfaces(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgPluggableStore", ["copyMessages()"]):
            self.assert_silent()
            self.assert_compat_error(type_="notice")

    def test_functions(self):
        patterns = ["mailnews.display.html_sanitizer.allowed_tags", "gPrefs()",
         "gHeaderParser()", "(msgComposeService()", "nsPrefBranch()",
         "(cvHeaderParser",]
        for pattern in patterns:
            self.run_regex_for_compat("var x = %s();" % pattern)
            self.assert_silent()
            assert self.compat_err.notices
            assert self.compat_err.compat_summary["errors"]

        # These patterns should not be flagged.
        for pattern in ["cvsPrefs()", "mailnews()",
                        "CollapseSectionHeaderators()",
                        "msgMailSession", "msgPrefs",]:
            self.run_regex_for_compat("var x = %s();" % pattern, is_js=True)
            self.assert_silent()
            self.assert_compat_silent()
