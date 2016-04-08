from helper import CompatTestCase
from validator.compat import FX47_DEFINITION


class TestFX47Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 47 are properly executed."""

    VERSION = FX47_DEFINITION

    def test_bnsIX509CertDB_method_changed(self):
        """https://github.com/mozilla/addons-server/issues/2221"""
        expected = 'Most methods in nsIX509CertDB had their unused arguments removed.'

        script = '''
            var certDB = Cc["@mozilla.org/security/x509certdb;1"]
                    .getService(Ci.nsIX509CertDB);
            certDB.importPKCS12File(null, nsIFile);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        # There are other checks because using nsIX509CertDB is
        # potentially dangerous.
        assert len(self.compat_err.warnings) == 4
        assert self.compat_err.warnings[3]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[3]['message'].startswith(expected)

        script = '''
            var certDB = Cc["@mozilla.org/security/x509certdb;1"]
                                        .getService(Ci.nsIX509CertDB);
            certdb.importCertsFromFile(null, fp.file, nsIX509Cert.CA_CERT);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        # There are other checks because using nsIX509CertDB is
        # potentially dangerous.
        assert len(self.compat_err.warnings) == 4
        assert self.compat_err.warnings[3]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[3]['message'].startswith(expected)

        script = 'const nsIX509CertDB = Components.interfaces.nsIX509CertDB;'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        # There are other checks because using nsIX509CertDB is
        # potentially dangerous.
        assert len(self.compat_err.warnings) == 3
        assert self.compat_err.warnings[2]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[2]['message'].startswith(expected)

    def test_changed_return_type(self):
        """https://github.com/mozilla/addons-server/issues/2220"""
        message = (
            'listTokens() and listSlots() now return '
            'nsISimpleEnumerator instead of nsIEnumerator.')

        script = 'let tokenList = gTokenDB.listTokens();'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = 'slot = belgiumEidPKCS11Module.listSlots().currentItem();'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = 'let slots = testModule.listSlots();'

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

    def test_gDevTools_moved(self):
        """https://github.com/mozilla/addons-server/issues/2219"""
        message = 'The gDevTools.jsm module should no longer be used.'

        script = 'Components.utils.import("resource:///modules/devtools/client/framework/gDevTools.jsm", ainspectorSidebar);'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'warning'
        assert self.compat_err.warnings[0]['message'].startswith(message)
