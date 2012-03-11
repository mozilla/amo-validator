from validator.errorbundler import ErrorBundle

from js_helper import TestCase


class TestWrappedJSObject(TestCase):
    """
    Tests related to XPCNativeWrapper's unwrap function and JS objects'
    wrappedJSObject property.
    """

    def test_pass(self):
        self.run_script("""
            var x = foo.wrappedJSObject;
            var y = XPCNativeWrapper.unwrap(foo);
        """)
        self.assert_silent()

    def assert_wrappedjs_failure(self):
        """A set of assertions for wrappedJSObject-related errors."""
        self.assert_failed(with_warnings=True)
        self.assert_got_errid(("testcases_javascript_jstypes", "JSObject_set",
                               "unwrapped_js_object"))

    def test_cant_assign(self):
        """Test that properties can't be assigned to unwrapped JS objects."""
        self.run_script("""
            var x = foo.wrappedJSObject;
            x.foo = "asdf";
        """)
        self.assert_wrappedjs_failure()

    def test_recursive_assign(self):
        """
        Test that properties can't be assigned to the members of unwrapped
        JS objects.
        """
        self.run_script("""
            var x = foo.wrappedJSObject;
            x.foo.bar.zap = "asdf";
        """)
        self.assert_wrappedjs_failure()

    def test_cant_assign_unwrap(self):
        """
        Test that properties can't be assigned to JS objects that were
        unwrapped via XPCNativeWrapper.unwrap().
        """
        self.run_script("""
            var x = XPCNativeWrapper.unwrap(foo);
            x.foo = "asdf";
        """)
        self.assert_wrappedjs_failure()

    def test_recursive_assign_unwrap(self):
        """
        Test that properties can't be assigned to the members of objects that
        were unwrapped via XPCNativeWrapper.unwrap().
        """
        self.run_script("""
            var x = XPCNativeWrapper.unwrap(foo);
            x.foo.bar.zap = "asdf";
        """)
        self.assert_wrappedjs_failure()

    def test_rewrapping(self):
        """Test that objects can be unwrapped and then rewrapped."""
        self.run_script("""
            var x = XPCNativeWrapper.unwrap(foo);
            x = XPCNativeWrapper(x);
            x.foo.bar.zap = "asdf";
        """)
        self.assert_silent()

    def test_rewrapping_from_wrappedjsobject(self):
        """
        Test that objects can be unwrapped and then rewrapped via the
        wrappedJSObject property.
        """
        self.run_script("""
            var x = foo.wrappedJSObject;
            x = XPCNativeWrapper(x);
            x.foo.bar.zap = "asdf";
        """)
        self.assert_silent()

    def test_unsafeWindow_banned(self):
        """Test that the unsafeWindow property is marked as dangerous."""

        self.run_script("""
        var x = unsafeWindow.foo.bar;
        """)
        self.assert_failed(with_warnings=True)

    def test_unsafeWindow_write_banned(self):
        """
        Test that writes tothe unsafeWindow property is marked as dangerous.
        """
        self.run_script("""
        unsafeWindow.foo.bar = "test";
        """)
        self.assert_failed(with_warnings=True)

