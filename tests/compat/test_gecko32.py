from helper import CompatTestCase
from validator.compat import FX32_DEFINITION


class TestFX32Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 32 are properly executed."""

    VERSION = FX32_DEFINITION

    def test_nsICache(self):
        self.run_script_for_compat('''
            Components.interfaces.nsICache.STORE_ANYWHERE;
        ''')
        self.assert_silent()
        self.assert_compat_error()

    def test_nsICacheService(self):
        for _ in self.run_xpcom_for_compat('nsICacheService',
                                           ['createSession']):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsICacheSession(self):
        for _ in self.run_xpcom_for_compat('nsICacheSession', ['foo']):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsICacheEntryDescriptor(self):
        for _ in self.run_xpcom_for_compat('nsICacheEntryDescriptor', ['foo']):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsICacheListener(self):
        for _ in self.run_xpcom_for_compat('nsICacheListener', ['foo']):
            self.assert_silent()
            self.assert_compat_error()

    def test_nsICacheVisitor(self):
        for _ in self.run_xpcom_for_compat('nsICacheVisitor', ['foo']):
            self.assert_silent()
            self.assert_compat_error()
