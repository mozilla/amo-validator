from helper import CompatTestCase
from validator.compat import FX21_DEFINITION


class TestFX21Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 21 are properly executed."""

    VERSION = FX21_DEFINITION

    def test_jsm(self):
        def test_pattern(self, pat):
            self.setUp()
            self.run_regex_for_compat(pat, is_js=True)
            self.assert_silent()
            self.assert_compat_error(type_="warning")

        yield test_pattern, self, "resource:///modules/foo/bar"
        yield test_pattern, self, "resource://gre/modules/HUDService.jsm"
        yield test_pattern, self, "resource://gre/modules/offlineAppCache.jsm"

    def test_jsm_pass(self):
        def test_pattern(self, pat):
            self.setUp()
            self.run_regex_for_compat(pat, is_js=True)
            self.assert_silent()
            self.assert_compat_silent()

        yield test_pattern, self, "resource:///foo/bar"
        yield test_pattern, self, "resource://gre/modules/HUDService"
        yield test_pattern, self, "resource://foo/modules/offlineAppCache.jsm"

    def test_nsINavHistoryService(self):
        self.run_regex_for_compat(
            "RESULT_TYPE_DYNAMIC_CONTAINER", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_onBeforeStuff(self):
        self.run_regex_for_compat("onBeforeDeleteURI", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")
