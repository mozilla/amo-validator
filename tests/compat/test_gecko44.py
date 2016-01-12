from helper import CompatTestCase
from validator.compat import FX44_DEFINITION


class TestFX44Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 44 are properly executed."""

    VERSION = FX44_DEFINITION

    def test_new_devtools_location_gre(self):
        self.run_script_for_compat("""
            var devtools = Cu.import("resource://gre/modules/devtools/shared/Loader.jsm", {}).devtools;
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_new_devtools_location_from_root(self):
        self.run_script_for_compat("""
            var devtools = Cu.import("resource:///modules/devtools/Target.jsm", {});
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_noSuchMethod_literal(self):
        self.run_script_for_compat("""
            var o = {
              __noSuchMethod__: function(id, args) {
                console.log(id, '(' + args.join(', ') + ')');
              }
          };
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_noSuchMethod_assignment(self):
        self.run_script_for_compat("""
            var o = {};
            o.__noSuchMethod__ = function(id, args) {
              console.log(id, '(' + args.join(', ') + ')');
            };
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_noSuchMethod_string_assignment(self):
        self.run_script_for_compat("""
            var o = {};
            o['__noSuchMethod__'] = function(id, args) {
              console.log(id, '(' + args.join(', ') + ')');
            };
        """)

    def test_getAllStyleSheets(self):
        self.run_script_for_compat(
            'let stylesheets = window.getAllStyleSheets(config.browser.contentWindow);'
        )
        self.assert_silent()
        self.assert_compat_error()
