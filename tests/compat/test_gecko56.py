from helper import CompatTestCase
from validator.compat import FX56_DEFINITION


class TestFX56Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 56 are properly executed."""

    VERSION = FX56_DEFINITION

    def test_showModalDialog_removed(self):
        """https://github.com/mozilla/amo-validator/issues/557"""
        expected = 'The showModalDialog function has been removed.'

        codes = [
          (
            'showModalDialog('
              '"http://developer.mozilla.org/samples/domref/showModalDialogBox.html",'
              '[1, 4], "dialogwidth: 450; dialogheight: 300; resizable: yes");'
          ),
          (
            'window.showModalDialog('
              '\'javascript:document.writeln("<script>alert(foo)" + "<" + "/script>")\');'
          )
        ]

        for code in codes:
          self.run_script_for_compat(code)

          assert not self.compat_err.notices
          assert not self.compat_err.errors

          self.assert_compat_error('warning', expected)
