from helper import CompatTestCase
from validator.compat import TB20_DEFINITION


class TestTB20Compat(CompatTestCase):
    """Test that compatibility tests for Thunderbird 20 are properly executed."""

    VERSION = TB20_DEFINITION

    def test_js_patterns(self):
        """Test that these patterns are flagged in Thunderbird 20."""
        self.setUp()
        self.run_regex_for_compat("var x = %s();" "GetWindowByWindowType")
        self.assert_compat_error(type_="notice")

    def test_nsIMsgAccount_identities(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgAccount", ["identities"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgAccountManager(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgAccountManager",
                ["allIdentities", "GetIdentitiesForServer", "accounts",
                 "GetServersForIdentity", "allServers"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgFolder_getExpansionArray(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgFolder", ["getExpansionArray"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgFilter(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgFilter", ["actionList", "getSortedActionList"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

    def test_nsIMsgFilterService_applyFiltersToFolders(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgFilterService", ["applyFiltersToFolders"]):
            self.assert_silent()
            self.assert_compat_error(type_="warning")

