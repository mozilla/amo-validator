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

    def test_geturiforkeyword_removed(self):
        """https://github.com/mozilla/amo-validator/issues/504"""
        expected = 'The getURIForKeyword function was removed.'

        script = '''
          let bmserv = Cc["@mozilla.org/browser/nav-bookmarks-service;1"].
                       getService(Ci.nsINavBookmarksService);
          if (bmserv.getURIForKeyword(alias.value))
            bduplicate = true;
        '''

        self.run_script_for_compat(script)
        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

    def test_openuriinnewntab_changed(self):
        """https://github.com/mozilla/amo-validator/issues/503"""
        expected = (
            'The _openURIInNewTab function was changed and now requires '
            'an nsIURI for the referrer.')

        script = '''
          let _original__openURIInNewTab = nsBrowserAccess._openURIInNewTab;

          nsBrowserAccess.prototype._openURIInNewTab = function(aURI, aReferrer, aReferrerPolicy, aIsPrivate,
                                                                aIsExternal, aForceNotRemote=false) {
            let browser = _original__openURIInNewTab.apply(nsBrowserAccess.prototype, arguments);
            if (!aIsExternal) {
              browser.setAttribute("diverted", "true");
            }
            return browser;
          };
        '''

        self.run_script_for_compat(script)
        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

    def test_nsIX509CertDB(self):
        """https://github.com/mozilla/amo-validator/issues/502"""
        expected = (
            'The nsIX509CertDB interface was changed so it no longer '
            'exposes the certificate nickname.')

        script = '''
            XmlMultiDSigUtil.mX509CertDB = Components.classes["@mozilla.org/security/x509certdb;1"]
                            .getService(Components.interfaces.nsIX509CertDB);
            signerCert = XmlMultiDSigUtil.mX509CertDB.findCertByNickname(null, signerCertNickname);
        '''

        self.run_script_for_compat(script)
        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

    def test_nsIPK11TokenDBfindTokenByName(self):
        """https://github.com/mozilla/amo-validator/issues/507"""
        expected = 'Calling findTokenByName("") is no longer valid.'

        script = '''
            Components.classes["@mozilla.org/security/pk11tokendb;1"]
                .getService(Components.interfaces.nsIPK11TokenDB)
                .findTokenByName("").logoutAndDropAuthenticatedResources();
        '''

        self.run_script_for_compat(script)
        assert not self.compat_err.notices
        assert not self.compat_err.errors

        self.assert_compat_error('warning', expected)

        # Make sure that we explicitly check for an empty first argument
        script = '''
            Components.classes["@mozilla.org/security/pk11tokendb;1"]
                .getService(Components.interfaces.nsIPK11TokenDB)
                .findTokenByName("not empty")
                .logoutAndDropAuthenticatedResources();
        '''

        self.run_script_for_compat(script)
        assert not self.compat_err.notices
        assert not self.compat_err.errors
        assert not self.compat_err.warnings
