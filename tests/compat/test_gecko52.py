import pytest

from helper import CompatTestCase
from validator.compat import FX52_DEFINITION


class TestFX52Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 52 are properly executed."""

    VERSION = FX52_DEFINITION

    def test_nsISupportsArray_deprecated(self):
        """https://github.com/mozilla/amo-validator/issues/493"""
        expected = (
            'The nsISupportsArray interface is deprecated and is being '
            'replaced by nsIArray.')

        script = '''
        var messages = Components.classes["@mozilla.org/supports-array;1"].createInstance(Components.interfaces.nsISupportsArray);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_warning('warning', expected)

    def test_mozDash_error(self):
        """https://github.com/mozilla/amo-validator/issues/492"""
        expected = 'The mozDash and mozDashOffset properties are no longer supported.'

        script = '''
            var canvas = document.getElementById('mycanvas');
            var ctx = canvas.getContext('2d');
            console.log(ctx.mozDash);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

    def test_mozDashOffset_error(self):
        """https://github.com/mozilla/amo-validator/issues/492"""
        expected = 'The mozDash and mozDashOffset properties are no longer supported.'

        script = '''
            var canvas = document.getElementById('mycanvas');
            var ctx = canvas.getContext('2d');
            console.log(ctx.mozDashOffset);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)
