from helper import CompatTestCase
from validator.compat import FX45_DEFINITION


class TestFX45Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 45 are properly executed."""

    VERSION = FX45_DEFINITION

    def test_nsIURIChecker_removed(self):
        variations = (
            'request.QueryInterface(Components.interfaces.nsIURIChecker);',
            'IURIChecker = Components.interfaces.nsIURIChecker;'
        )
        for variation in variations:
            self.run_script_for_compat(variation)

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            assert len(self.compat_err.warnings) == 1
            assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
            assert (
                self.compat_err.warnings[0]['message']
                == 'The nsIURIChecker interface has been removed')

    def test_identity_interface_changed(self):
        variations = (
            'var gProxyFavIcon = document.getElementById("page-proxy-favicon");',
            'var iconURL = gProxyFavIcon.getAttribute("src");'
        )
        for variation in variations:
            self.run_script_for_compat(variation)

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            assert len(self.compat_err.warnings) == 1
            assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
            assert self.compat_err.warnings[0]['message'].startswith(
                'The site identity interface has changed')

    def test_removeAllPages_deprecated(self):
        variations = (
            'historyManager.removeAllPages(); ',
            'historyService.removeAllPages(); '
        )
        for variation in variations:
            self.run_script_for_compat(variation)

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            assert len(self.compat_err.warnings) == 1
            assert self.compat_err.warnings[0]['compatibility_type'] == 'warning'
            assert (
                self.compat_err.warnings[0]['message'] ==
                'The removeAllPages function is now deprecated.')
