from helper import CompatTestCase
from validator.compat import FX39_DEFINITION


class TestFX39Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 39 are properly executed."""

    VERSION = FX39_DEFINITION

    def test_noSuchMethod_literal(self):
        self.run_script_for_compat("""
            var o = {
              __noSuchMethod__: function(id, args) {
                console.log(id, '(' + args.join(', ') + ')');
              }
          };
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_noSuchMethod_assignment(self):
        self.run_script_for_compat("""
            var o = {};
            o.__noSuchMethod__ = function(id, args) {
              console.log(id, '(' + args.join(', ') + ')');
            };
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_noSuchMethod_string_assignment(self):
        self.run_script_for_compat("""
            var o = {};
            o['__noSuchMethod__'] = function(id, args) {
              console.log(id, '(' + args.join(', ') + ')');
            };
        """)
        self.assert_silent()
        self.assert_compat_warning(type_='warning')

    def test_sendAsBinary(self):
        self.run_script_for_compat("""
           var xhr = new XMLHttpRequest();
           xhr.sendAsBinary('foo');
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_lightweightThemes_usedThemes(self):
        self.run_script_for_compat("""
           var value = getPermission('lightweightThemes.usedThemes');
        """)
        self.assert_silent()
        self.assert_compat_error()

    def test_lightweightThemes_isThemeSelected(self):
        self.run_script_for_compat("""
           var value = getPermission('lightweightThemes.isThemeSelected');
        """)
        self.assert_silent()
        self.assert_compat_error()
