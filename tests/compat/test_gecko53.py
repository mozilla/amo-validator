from helper import CompatTestCase
from validator.compat import FX53_DEFINITION


class TestFX53Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 53 are properly executed."""

    VERSION = FX53_DEFINITION

    def test_splitmenu_element_removed(self):
        """https://github.com/mozilla/amo-validator/issues/506"""
        expected = 'The splitmenu element has been removed.'

        invalid = '''
            splitmenu {
                -moz-binding: url("chrome://browser/content/urlbarBindings.xml#splitmenu");
            }
        '''

        valid = '''
            .splitmenu-menuitem {
              -moz-binding: url("chrome://global/content/bindings/menu.xml#menuitem");
              list-style-image: inherit;
              -moz-image-region: inherit;
            }
        '''

        self.run_regex_for_compat(invalid, is_js=False)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

        self.reset()

        self.run_regex_for_compat(valid, is_js=False)

        assert not self.compat_err.notices
        assert not self.compat_err.errors
        assert not self.compat_err.warnings

    def test_moz_calc_removed(self):
        """https://github.com/mozilla/amo-validator/issues/505"""
        expected = 'The -moz-calc function has been removed.'

        invalid = [
            'min-width: -moz-calc(6em - 14px);',
            'background-size: -moz-calc(100% - 2px) -moz-calc(100% - 2px);',
            '-moz-radial-gradient(-moz-calc(100px + -25px) top, red, blue)',
        ]

        for script in invalid:
            self.run_regex_for_compat(script, is_js=False)
            assert not self.compat_err.notices
            assert not self.compat_err.errors
            self.assert_compat_warning('warning', expected)

            self.reset()
