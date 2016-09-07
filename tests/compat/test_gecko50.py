import pytest

from helper import CompatTestCase
from validator.compat import FX50_DEFINITION


class TestFX50Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 50 are properly executed."""

    VERSION = FX50_DEFINITION

    def test_nsIX509Cert_removed(self):
        """https://github.com/mozilla/addons-server/issues/3408"""
        expected = (
            'The methods getUsagesArray, requestUsagesArrayAsync, and '
            'getUsagesString are no longer supported.')

        script = '''
            var certdb = Components.classes["@mozilla.org/security/x509certdb;1"].
                getService(Components.interfaces.nsIX509CertDB);
            var cert = certdb.findCertByDBKey(
                tgt.parentNode.firstChild.getAttribute("display"),
                null);

            cert.QueryInterface(Components.interfaces.nsIX509Cert);
            cert.getUsagesArray();
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_nsIX509Cert_requestUsagesArrayAsync_removed(self):
        """https://github.com/mozilla/addons-server/issues/3408"""
        expected = (
            'The methods getUsagesArray, requestUsagesArrayAsync, and '
            'getUsagesString are no longer supported.')

        script = '''
            var certdb = Components.classes["@mozilla.org/security/x509certdb;1"].
                getService(Components.interfaces.nsIX509CertDB);
            var cert = certdb.findCertByDBKey(
                tgt.parentNode.firstChild.getAttribute("display"),
                null);

            cert.QueryInterface(Components.interfaces.nsIX509Cert2);
            cert.requestUsagesArrayAsync();
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_nsIX509Cert_getUsagesString(self):
        """https://github.com/mozilla/addons-server/issues/3408"""
        expected = (
            'The methods getUsagesArray, requestUsagesArrayAsync, and '
            'getUsagesString are no longer supported.')

        script = '''
            var certdb = Components.classes["@mozilla.org/security/x509certdb;1"].
                getService(Components.interfaces.nsIX509CertDB);
            var cert = certdb.findCertByDBKey(
                tgt.parentNode.firstChild.getAttribute("display"),
                null);

            cert.QueryInterface(Components.interfaces.nsIX509Cert3);
            cert.getUsagesString();
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_events_removed_html_xul(self):
        """https://github.com/mozilla/addons-server/issues/3407"""
        expected = (
            'The draggesture and dragdrop events are no longer supported. '
            'You should use the standard equivalents instead: '
            'dragstart and drop.')

        events = ('draggesture', 'dragdrop', 'ondraggesture', 'ondragdrop')

        base = '''
            <treechildren
                {0}="nsDragAndDrop.startDrag(event, foxclocks.mainManager)"/>
        '''

        for event in events:
            self.run_regex_for_compat(base.format(event), is_js=False)

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            warning = [
                msg for msg in self.compat_err.warnings
                if msg['message'].startswith(expected)]
            assert warning
            assert warning[0]['compatibility_type'] == 'error'

    def test_events_removed_js(self):
        """https://github.com/mozilla/addons-server/issues/3407"""
        expected = (
            'The draggesture and dragdrop events are no longer supported. '
            'You should use the standard equivalents instead: '
            'dragstart and drop.')

        events = ('draggesture', 'dragdrop', 'ondraggesture', 'ondragdrop')

        base = '''
            $.on('{0}');
        '''

        for event in events:
            self.run_regex_for_compat(base.format(event))

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            warning = [
                msg for msg in self.compat_err.warnings
                if msg['message'].startswith(expected)]
            assert warning
            assert warning[0]['compatibility_type'] == 'error'
