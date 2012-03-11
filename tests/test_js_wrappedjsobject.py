from validator.errorbundler import ErrorBundle

from js_helper import TestCase


def wrapped_js_failure(function):
    """A decorator to assert that wrappedJSObject-related errors occurred."""

    def wrap(self):
        function(self)
        self.assert_failed(with_warnings=True)
        self.assert_got_errid(("testcases_javascript_jstypes", "JSObject_set",
                               "unwrapped_js_object"))

    wrap.__name__ = function.__name__
    return wrap


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

    @wrapped_js_failure
    def test_cant_assign(self):
        """Test that properties can't be assigned to unwrapped JS objects."""
        self.run_script("""
            var x = foo.wrappedJSObject;
            x.foo = "asdf";
        """)

    @wrapped_js_failure
    def test_recursive_assign(self):
        """
        Test that properties can't be assigned to the members of unwrapped
        JS objects.
        """
        self.run_script("""
            var x = foo.wrappedJSObject;
            x.foo.bar.zap = "asdf";
        """)

    @wrapped_js_failure
    def test_cant_assign_unwrap(self):
        """
        Test that properties can't be assigned to JS objects that were
        unwrapped via XPCNativeWrapper.unwrap().
        """
        self.run_script("""
            var x = XPCNativeWrapper.unwrap(foo);
            x.foo = "asdf";
        """)

    @wrapped_js_failure
    def test_recursive_assign_unwrap(self):
        """
        Test that properties can't be assigned to the members of objects that
        were unwrapped via XPCNativeWrapper.unwrap().
        """
        self.run_script("""
            var x = XPCNativeWrapper.unwrap(foo);
            x.foo.bar.zap = "asdf";
        """)

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

