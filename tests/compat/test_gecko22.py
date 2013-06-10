from helper import CompatTestCase
from validator.compat import FX22_DEFINITION


class TestFX22Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 22 are properly executed."""

    VERSION = FX22_DEFINITION

    def test_nsigh2(self):
        self.run_regex_for_compat("nsIGlobalHistory2", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_nsilms(self):
        self.run_regex_for_compat("nsILivemarkService", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_mpat(self):
        self.run_regex_for_compat("markPageAsTyped", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_favicon(self):
        self.run_regex_for_compat("setFaviconUrlForPage", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_nsitv(self):
        self.run_regex_for_compat("getRowProperties", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_nsipb(self):
        self.run_regex_for_compat("nsIPrivateBrowsingService", is_js=True)
        self.assert_silent()
        self.assert_compat_error(type_="warning")

    def test_fullZoom(self):
        self.run_regex_for_compat("fullZoom", is_js=True)
        self.assert_silent()
        self.assert_compat_error()

    def test_userdata(self):
        self.run_regex_for_compat("getUserData", is_js=True)
        self.assert_silent()
        self.assert_compat_warning()

    def test_tooltip(self):
        self.run_regex_for_compat("FillInHTMLTooltip", is_js=True)
        self.assert_silent()
        self.assert_compat_warning()
