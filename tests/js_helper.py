import sys

from nose.tools import eq_

import helper
from helper import MockXPI
from validator.errorbundler import ErrorBundle
from validator.outputhandlers.shellcolors import OutputHandler
import validator.testcases.content
import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True


def _do_test(path):
    "Performs a test on a JS file"

    script = open(path).read()
    return _do_test_raw(script, path)


def _do_test_raw(script, path="foo.js", bootstrap=False, ignore_pollution=True,
                 detected_type=None, jetpack=False):
    "Performs a test on a JS file"

    err = ErrorBundle(instant=True)
    if jetpack:
        err.metadata["is_jetpack"] = True

    err.handler = OutputHandler(sys.stdout, True)
    err.supported_versions = {}
    if bootstrap:
        err.save_resource("em:bootstrap", True)
    if detected_type:
        err.detected_type = detected_type

    validator.testcases.content._process_file(
            err, MockXPI(), path, script, path.lower(), not ignore_pollution)
    if err.final_context is not None:
        print err.final_context.output()

    return err


def _do_real_test_raw(script, path="foo.js", versions=None, detected_type=None,
                      metadata=None, resources=None, jetpack=False):
    """Perform a JS test using a non-mock bundler."""

    err = ErrorBundle(for_appversions=versions or {})
    if detected_type:
        err.detected_type = detected_type
    if metadata is not None:
        err.metadata = metadata
    if resources is not None:
        err.resources = resources
    if jetpack:
        err.metadata["is_jetpack"] = True

    validator.testcases.content._process_file(err, MockXPI(), path, script,
                                              path.lower())
    return err


def _get_var(err, name):
    return err.final_context.data[name].get_literal_value()


def _do_test_scope(script, vars):
    """Test the final scope of a script against a set of variables."""
    scope = _do_test_raw(script)
    for var, value in vars.items():
        print "Testing %s" % var
        var_val = _get_var(scope, var)
        if isinstance(var_val, float):
            var_val *= 100000
            var_val = round(var_val)
            var_val /= 100000
        eq_(var_val, value)


class TestCase(helper.TestCase):
    """A TestCase object with specialized functions for JS testing."""

    def setUp(self):
        self.file_path = "foo.js"
        self.final_context = None
        super(TestCase, self).setUp()

    def run_script_from_file(self, path):
        """
        Run the standard set of JS engine tests on a script found at the
        location in `path`.
        """
        with open(path) as script_file:
            return self.run_script(script_file.read())

    def run_script(self, script, expose_pollution=False):
        """
        Run the standard set of JS engine tests on the script passed via
        `script`.
        """
        if self.err is None:
            self.setup_err()
        self.err.supported_versions = {}

        validator.testcases.content._process_file(self.err, MockXPI(),
                                                  self.file_path, script,
                                                  self.file_path.lower(),
                                                  expose_pollution)
        if self.err.final_context is not None:
            print self.err.final_context.output()
            self.final_context = self.err.final_context

    def get_var(self, name):
        """
        Return the value of a variable from the final script context.
        """
        try:
            return self.final_context.data[name].get_literal_value()
        except KeyError:
            raise ("Test seeking variable (%s) not found in final context." %
                       name)

    def assert_var_eq(self, name, value):
        """
        Assert that the value of a variable from the final script context
        contains the value specified.
        """
        self.assertEqual(self.get_var(name), value)

