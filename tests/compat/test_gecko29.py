from helper import CompatTestCase
from validator.compat import FX29_DEFINITION


class TestFX29Compat(CompatTestCase):
    """Test that compatibility tests for Firefox 29 are properly executed."""

    VERSION = FX29_DEFINITION

    def test_callback_warning_add(self):
        self.run_script_for_compat(
            'PlacesUtils.livemarks.addLivemark("foo", bar);')
        self.assert_silent()
        self.assert_compat_warning("warning")

    def test_callback_warning_remove(self):
        self.run_script_for_compat(
            'PlacesUtils.livemarks.removeLivemark("foo", bar);')
        self.assert_silent()
        self.assert_compat_warning("warning")

    def test_callback_warning_get(self):
        self.run_script_for_compat('''
            PlacesUtils.livemarks.getLivemark("foo", function () {
                alert("done!");
            });
        ''')
        self.assert_silent()
        self.assert_compat_warning("warning")

    def test_no_callback_no_warning_add(self):
        self.run_script_for_compat(
            'var promise = PlacesUtils.livemarks.addLivemark("foo");')
        self.assert_silent()
        self.assert_compat_silent()

    def test_no_callback_no_warning_remove(self):
        self.run_script_for_compat('''
            var promise = PlacesUtils.livemarks.removeLivemark({
                foo: "foo",
                bar: "bar",
            });''')
        self.assert_silent()
        self.assert_compat_silent()

    def test_no_callback_no_warning_get(self):
        self.run_script_for_compat(
            'var promise = PlacesUtils.livemarks.getLivemark("foo");')
        self.assert_silent()
        self.assert_compat_silent()
