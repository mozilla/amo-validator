from helper import CompatTestCase
from validator.compat import FX30_DEFINITION


class TestFX30Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 30 are properly executed."""

    VERSION = FX30_DEFINITION

    def test_resources(self):
        def test_pattern(self, pat):
            self.setUp()
            self.run_regex_for_compat(pat, is_js=True)
            self.assert_silent()
            self.assert_compat_error(type_="warning")

        yield test_pattern, self, "resource://gre/modules/AddonRepository.jsm"
        yield (test_pattern, self,
               "resource://gre/modules/LightweightThemeImageOptimizer.jsm")
        yield test_pattern, self, "resource://gre/modules/XPIProvider.jsm"
        yield (test_pattern, self,
               "resource://gre/modules/AddonUpdateChecker.jsm")
        yield test_pattern, self, "resource://gre/modules/AddonLogging.jsm"
        yield test_pattern, self, "resource://gre/modules/PluginProvider.jsm"
        yield (test_pattern, self,
               "resource://gre/modules/AddonRepository_SQLiteMigrator.jsm")
        yield test_pattern, self, "resource://gre/modules/XPIProviderUtils.js"
        yield (test_pattern, self,
               "resource://gre/modules/SpellCheckDictionaryBootstrap.js")
