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

    def test_setting__proto__(self):
        self.run_script_for_compat("var myObj = {}; myObj.__proto__ = {};")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_reading__proto__(self):
        self.run_script_for_compat("console.log(myObj.__proto__.foo);")
        self.assert_silent()
        self.assert_compat_silent()

    def test_setPrototypeOf_usage(self):
        self.run_script_for_compat("Object.setPrototypeOf(myObj, {});")
        self.assert_silent()
        self.assert_compat_warning(type_="warning")

    def test_object_create_okay(self):
        self.run_script_for_compat("""
        // Use this instead of obj.__proto__ = {} or
        // Object.setPrototypeOf(foo, bar).
        Object.create({});""")
        self.assert_silent()
        self.assert_compat_silent()

    def test_DOM_VK_ENTER_usage(self):
        self.run_script_for_compat("""
        var foo = KeyboardEvent.DOM_VK_ENTER;
        """)
        self.assert_silent()
        self.assert_compat_warning(type_="warning")
