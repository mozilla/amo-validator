from helper import CompatTestCase
from validator.compat import FX48_DEFINITION


class TestFX48Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 48 are properly executed."""

    VERSION = FX48_DEFINITION

    def test_nsIIOService_newChannel_deprecated(self):
        """https://github.com/mozilla/addons-server/issues/2679"""
        expected = (
            'The "newChannel" functions have been deprecated in favor of '
            'their new versions (ending with 2).')

        script = '''
            var iOService = Components.classes["@mozilla.org/network/io-service;1"]
                .getService(Components.interfaces.nsIIOService);
            let channel = iOService.newChannel();
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'warning'

    def test_nsIIOService_newChannelFromURI_deprecated(self):
        """https://github.com/mozilla/addons-server/issues/2679"""
        expected = (
            'The "newChannel" functions have been deprecated in favor of '
            'their new versions (ending with 2).')

        script = '''
            var io = Components.classes["@mozilla.org/network/io-service;1"]
                .getService(Components.interfaces["nsIIOService"]);
            reqObj = io.newChannelFromURI(uri);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'warning'

    def test_nsIIOService_newChannelFromURIWithProxyFlags(self):
        """https://github.com/mozilla/addons-server/issues/2679"""
        expected = (
            'The "newChannel" functions have been deprecated in favor of '
            'their new versions (ending with 2).')

        script = '''
            var iOService = Components.classes["@mozilla.org/network/io-service;1"]
                .getService(Components.interfaces.nsIIOService);
            var channel = iOService.newChannelFromURIWithProxyFlags(aboutURI);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'warning'
