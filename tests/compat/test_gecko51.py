import pytest

from helper import CompatTestCase
from validator.compat import FX51_DEFINITION


class TestFX51Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 50 are properly executed."""

    VERSION = FX51_DEFINITION

    def test_mozIAsyncFavicons_setAndFetchFaviconForPage_changed(self):
        """https://github.com/mozilla/amo-validator/issues/475"""
        expected = (
            'The methods setAndFetchFaviconForPage and '
            'replaceFaviconDataFromDataURL now default to using a null '
            'principal for security reasons. An appropriate principal should '
            'be passed if different behavior is required.')

        script = '''
            var ioService = Components.classes["@mozilla.org/network/io-service;1"].
                getService(Components.interfaces.nsIIOService);
            var pageUri = ioService.newURI('http://mozilla.org', 'utf-8', 'mozilla.org');
            var faviconUri = ioService.newURI('http://mozilla.org/fav.ico', 'utf-8', 'mozilla.org');

            var faviconService = Components.classes["@mozilla.org/browser/favicon-service;1"].
                getService(Components.interfaces.nsIFaviconService).
                QueryInterface(Components.interfaces.mozIAsyncFavicons);
            faviconService.setAndFetchFaviconForPage(pageUri, faviconUri, false, faviconService.FAVICON_LOAD_NON_PRIVATE);
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'warning'

    def test_mozIAsyncFavicons_replaceFaviconDataFromDataURL_changed(self):
        """https://github.com/mozilla/amo-validator/issues/475"""
        expected = (
            'The methods setAndFetchFaviconForPage and '
            'replaceFaviconDataFromDataURL now default to using a null '
            'principal for security reasons. An appropriate principal should '
            'be passed if different behavior is required.')

        script = '''
            var ioService = Components.classes["@mozilla.org/network/io-service;1"].
                  getService(Components.interfaces.nsIIOService);
            var faviconUri = ioService.newURI('http://mozilla.org/fav.ico', 'utf-8', 'mozilla.org');

            var faviconService = Components.classes["@mozilla.org/browser/favicon-service;1"].
                     getService(Components.interfaces.nsIFaviconService).
                     QueryInterface(Components.interfaces.mozIAsyncFavicons);
            faviconService.replaceFaviconDataFromDataURL(faviconUri, 'data:base64/png');
        '''

        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [msg for msg in self.compat_err.warnings if msg['message'] == expected]
        assert warning
        assert warning[0]['compatibility_type'] == 'warning'

    def test_BrowserOpenNewTabOrWindow_removed(self):
        """https://github.com/mozilla/amo-validator/issues/473"""
        expected = (
            'The function BrowserOpenNewTabOrWindow has been removed.')

        script = '''
            window.BrowserOpenNewTabOrWindow();
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [
            msg for msg in self.compat_err.warnings
            if msg['message'].startswith(expected)]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_mozVisibilityState_unprefixed(self):
        """https://github.com/mozilla/amo-validator/issues/474"""
        expected = (
            'The mozVisibilityState and mozHidden properties are no longer '
            'prefixed.')

        script = '''
            var x = document.createElement('div');
            x.mozVisibilityState = true;
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [
            msg for msg in self.compat_err.warnings
            if msg['message'].startswith(expected)]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_mozHidden_unprefixed(self):
        """https://github.com/mozilla/amo-validator/issues/474"""
        expected = (
            'The mozVisibilityState and mozHidden properties are no longer '
            'prefixed.')

        script = '''
            var x = document.createElement('div');
            x.mozHidden = true;
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [
            msg for msg in self.compat_err.warnings
            if msg['message'].startswith(expected)]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'

    def test_onButtonClick_changed(self):
        """https://github.com/mozilla/amo-validator/issues/476"""
        expected = 'The function onButtonClick is now asynchronous.'

        script = '''
            var f = function() { return true };
            var x = document.createElement('div');
            x.onButtonClick(f);
        '''
        self.run_script_for_compat(script)

        assert not self.compat_err.notices
        assert not self.compat_err.errors

        warning = [
            msg for msg in self.compat_err.warnings
            if msg['message'].startswith(expected)]
        assert warning
        assert warning[0]['compatibility_type'] == 'error'
