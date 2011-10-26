import sys

from nose.tools import eq_

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
                 detected_type=None):
    "Performs a test on a JS file"

    err = ErrorBundle(instant=True)
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
                      metadata=None, resources=None):
    """Perform a JS test using a non-mock bundler."""

    err = ErrorBundle(for_appversions=versions or {})
    if detected_type:
        err.detected_type = detected_type
    if metadata is not None:
        err.metadata = metadata
    if resources is not None:
        err.resources = resources

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

