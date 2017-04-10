from helper import CompatTestCase
from validator.compat import FX54_DEFINITION


class TestFX54Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 54 are properly executed."""

    VERSION = FX54_DEFINITION

    def test_formhistory2_removed(self):
        """https://github.com/mozilla/amo-validator/issues/523"""
        expected = (
            'The nsIFormHistory2 interface has been removed. You can use '
            'FormHistory.jsm instead.')

        code = '''
            Components.classes["@mozilla.org/satchel/form-history;1"].getService(Components.interfaces.nsIFormHistory2)
        '''

        self.run_script_for_compat(code)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

    def test_moz_appearance(self):
        """https://github.com/mozilla/amo-validator/issues/524"""
        expected = '-moz-appearance can only be used in chrome stylesheets.'

        invalid = '-moz-border-radius: 0px; -moz-appearance:textfield;'

        self.run_regex_for_compat(invalid, is_js=False)
        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_warning('warning', expected)
