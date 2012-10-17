from helper import CompatTestCase
from validator.compat import TB16_DEFINITION


class TestTB16Compat(CompatTestCase):
    """
    Test that compatibility tests for Thunderbird 16 are properly executed.
    """

    VERSION = TB16_DEFINITION

    def test_nsIMsgCloudFileProvider(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgCloudFileProvider",
                ["uploadFile()", "urlForFile()", "cancelFileUpload()",
                 "deleteFile()"]):
            self.assert_silent()
            self.assert_compat_error

    def test_nsIAbLDAPDirectory(self):
        for method in self.run_xpcom_for_compat(
            "nsIAbLDAPDirectory", ["replicationFile"]):
            self.assert_silent()
            self.assert_compat_error

    def test_nsIMsgIncomingServer(self):
        for method in self.run_xpcom_for_compat(
                "nsIMsgIncomingServer",
                ["setDefaultLocalPath", "getFileValue", "setFileValue"]):
            self.assert_silent()
            self.assert_compat_error

    def test_nsiRssIncomingServer(self):
        for method in self.run_xpcom_for_compat(
                "nsiRssIncomingServer",
                ["subscriptionsDataSourcePath", "feedItemsDataSourcePath"]):
            self.assert_silent()
            self.assert_compat_error

    def test_nsiMsgFilterService(self):
        for method in self.run_xpcom_for_compat(
                "nsiMsgFilterService",
                ["OpenFilterList", "SaveFilterList"]):
            self.assert_silent()
            self.assert_compat_error

    def test_js_patterns(self):
        """Test that these js patterns are flagged in Thunderbird 16."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern)
            self.assert_compat_error(type_="notice")

   
        yield test_pattern, self, "(parseAdoptedMsgLine"
        yield test_pattern, self, " normalEndMsgWriteStream"

    def test_unflagged_patterns(self):
        """Test that these js patterns are _NOT_ flagged in Thunderbird 16."""
        def test_pattern(self, pattern):
            self.setUp()
            self.run_regex_for_compat("var x = %s();" % pattern)
            self.assert_compat_silent()

        yield test_pattern, self, "aparseAdoptedMsgLine"
        yield test_pattern, self, "abnormalEndMsgWriteStream"
