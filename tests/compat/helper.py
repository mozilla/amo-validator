from ..helper import RegexTestCase
from ..js_helper import TestCase as JSTestCase


class CompatTestCase(JSTestCase, RegexTestCase):
    """
    A TestCase object which aids in running tests regarding compatibility
    tests. It is expected that you will supply a static member `VERSION`
    describing the version(s) of Gecko that these tests apply to.
    """

    def setUp(self, *args, **kwargs):
        super(CompatTestCase, self).setUp(*args, **kwargs)

    def run_script_for_compat(self, script, expose_pollution=False):
        """
        Test a script with and without version restrictions to determine
        whether it properly raises JavaScript compatibility messages.
        """
        self._run_member_for_compat(
            lambda: self.run_script(script, expose_pollution))

    def run_xpcom_for_compat(self, interface, methods):
        """Yields after each method has been run as a script. Used to test that
        XPCOM members are properly flagged for compatibility tests.

        - `interface` should be the name of the XPCOM interface.
        - `methods` should be the member to test. It may be a simple reference
          to a member (i.e.: `foo`) or an action upon a member (i.e.:
          `foo('bar')` or `foo["bar"] = "zap"`).

        """

        script = """
        var x = Components.classes[""].createInstance(Components.interfaces.%s);
        x.%%s;
        """ % interface

        for method in methods:
            self.run_script_for_compat(script % method)
            yield

    def run_regex_for_compat(self, input, is_js=False):
        """Test an input with and without version restrictions to determine
        whether it properly raises regex compatibility messages.

        """
        self._run_member_for_compat(
            lambda: self.run_regex(input, is_js=is_js))

    def _run_member_for_compat(self, method):
        # Run the method without version restrictions.
        self.setup_err()
        method()

        # Store away that error bundle to prepare for the next error bundle.
        standard_err = self.err
        self.err = None

        # Run the method again with version restrictions.
        self.setup_err(for_appversions=self.VERSION)
        method()

        self.compat_err = self.err
        self.err = standard_err

    def assert_compat_silent(self):
        """Assert that no compatibility messages have been raised."""
        assert not any(self.compat_err.compat_summary.values()), \
                'Got %s' % self.compat_err.compat_summary

    def assert_compat_error(self, type_='warning', expected_message=None):
        """Assert that a compat error was raised as a message of type `type_`.

        """
        self._assert_compat_type('error', type_, expected_message)

    def assert_compat_warning(self, type_='notice', expected_message=None):
        """Assert that a compat warning was raised as a message of type
        `type_`.

        """
        self._assert_compat_type('warning', type_, expected_message)

    def _assert_compat_type(self, compat_type, type_, expected_message=None):
        print self.compat_err.print_summary()
        message_collection = {'error': self.compat_err.errors,
                              'warning': self.compat_err.warnings,
                              'notice': self.compat_err.notices}[type_]
        assert message_collection, \
            'No %ss were raised in the compatibility test.' % type_
        is_error = any(
            m['compatibility_type'] == compat_type
            for m in message_collection)

        assert is_error, ('No %ss that raise a compatibility %s were found.' %
                          (type_, compat_type))

        if expected_message is not None:
            has_message = any(
                msg for msg in message_collection
                if msg['message'] == expected_message)
            assert has_message, ('No message \'%s\' found.' % expected_message)
