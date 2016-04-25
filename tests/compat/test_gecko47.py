from helper import CompatTestCase
from validator.compat import FX47_DEFINITION


class TestFX47Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 47 are properly executed."""

    VERSION = FX47_DEFINITION

    def test_bnsIX509CertDB_method_changed(self):
        """https://github.com/mozilla/addons-server/issues/2221"""
        expected = (
            'Most methods in nsIX509CertDB had their unused '
            'arguments removed.')

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
        warning = [x for x in self.compat_err.warnings if x['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

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
        warning = [x for x in self.compat_err.warnings if x['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'


        script = 'const nsIX509CertDB = Components.interfaces.nsIX509CertDB;'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        # There are other checks because using nsIX509CertDB is
        # potentially dangerous.
        warning = [x for x in self.compat_err.warnings if x['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_changed_return_type(self):
        """https://github.com/mozilla/addons-server/issues/2220"""
        message = (
            'listTokens(), listModules() and listSlots() now return '
            'nsISimpleEnumerator instead of nsIEnumerator.')

        script = '''
            var db = Components.classes["@mozilla.org/security/pk11tokendb;1"]
                        .getService(Components.interfaces.nsIPK11TokenDB);
            var modules = db.listTokens();
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = '''
            var db = Components.classes["@mozilla.org/security/pkcs11moduledb;1"]
                        .getService(Components.interfaces.nsIPKCS11ModuleDB);
            var modules = db.listModules();
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = '''
            var modules = modules.QueryInterface(Components.interfaces.nsIPKCS11Module);
            modules.listSlots();
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = 'var modules = mylib.listModules();'
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors
        assert not self.compat_err.warnings

    def test_gDevTools_moved(self):
        """https://github.com/mozilla/addons-server/issues/2219"""
        message = 'The gDevTools.jsm module should no longer be used.'

        script = (
            'Components.utils.import("resource:///modules/devtools/client'
            '/framework/gDevTools.jsm", ainspectorSidebar);')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'warning'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        # Test that we actually match on "." and not "any character"
        script = (
            'Components.utils.import("resource:///modules/devtools/client'
            '/framework/gDevTools_jsm", ainspectorSidebar);')
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors
        assert not self.compat_err.warnings

    def test_FUEL_library_removed(self):
        """https://github.com/mozilla/addons-server/issues/2218"""
        message = 'The FUEL library is no longer supported.'

        script = ('var app = Components'
                  '.classes["@mozilla.org/fuel/application;1"]'
                  '.getService(Components.interfaces.fuelIApplication);')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = (
            'var nowDebug = !!Application.prefs.get'
            '("extensions.hatenabookmark.debug.log").value;')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        # Make sure the regex isn't too wide
        script = 'var application = "something not so serious";'

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors
        assert not self.compat_err.warnings

    def test_about_customizing_removed(self):
        """https://github.com/mozilla/addons-server/issues/2217"""
        message = 'The customization panel is no longer loaded via about:customizing'

        script = (
            '// * modified from: resource:///modules/'
            'CustomizationTabPreloader.jsm')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = (
            '// * ensurePreloading starts the preloading of the '
            'about:customizing')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)

        script = (
            'Components.utils.import("resource:///modules/'
            'CustomizationTabPreloader.jsm");')

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        assert len(self.compat_err.warnings) == 1
        assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
        assert self.compat_err.warnings[0]['message'].startswith(message)
