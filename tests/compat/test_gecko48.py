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

    def test_Proxy_createFunction_removed(self):
        """https://github.com/mozilla/addons-server/issues/2678"""
        expected = 'Proxy.create and Proxy.createFunction are no longer supported.'

        script = '''
             function f() { "use strict"; return this; }

            var p = Proxy.createFunction(f, f);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_Proxy_create_removed(self):
        """https://github.com/mozilla/addons-server/issues/2678"""
        expected = 'Proxy.create and Proxy.createFunction are no longer supported.'

        script = '''
            var handler = {
                getPropertyDescriptor(name) {
                    /* toSource may be called to generate error message. */
                    assertEq(name, "toSource");
                    return { value: () => "foo" };
                }
            };

            var proxiedFunctionPrototype = Proxy.create(handler, Function.prototype, undefined);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'
