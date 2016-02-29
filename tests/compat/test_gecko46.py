from helper import CompatTestCase
from validator.compat import FX46_DEFINITION


class TestFX46Compat(CompatTestCase):
    """Test that compatibility tests for Gecko 46 are properly executed."""

    VERSION = FX46_DEFINITION

    def test_mTab_renames(self):
        variations = (
            'filter.removeProgressListener(this.mTabListeners[index]);',
            'let tabListener = browser.mTabListeners[selectedIndex];',
            'const filter = this.mTabFilters[index];',
            'var filter = gBrowser.mTabFilters[targetPos];',
        )
        for variation in variations:
            self.run_script_for_compat(variation)

            assert not self.compat_err.notices
            assert not self.compat_err.errors

            assert len(self.compat_err.warnings) == 1
            assert self.compat_err.warnings[0]['compatibility_type'] == 'error'
            assert self.compat_err.warnings[0]['message'].startswith(
                'mTabListeners and mTabFilters are now Map objects')
