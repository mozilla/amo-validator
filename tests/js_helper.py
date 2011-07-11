from nose.tools import eq_

from validator.errorbundler import ErrorBundle
import validator.testcases.scripting
validator.testcases.scripting.traverser.DEBUG = True


def _do_test(path):
    "Performs a test on a JS file"

    script = open(path).read()
    return _do_test_raw(script, path)


def _do_test_raw(script, path="foo", bootstrap=False, ignore_pollution=True,
                 detected_type=None):
    "Performs a test on a JS file"

    err = validator.testcases.scripting.traverser.MockBundler()
    if bootstrap:
        err.save_resource("em:bootstrap", True)
    if detected_type:
        err.detected_type = detected_type
    if ignore_pollution:
        validator.testcases.scripting.traverser.IGNORE_POLLUTION = True

    validator.testcases.scripting.test_js_file(err, path, script)
    validator.testcases.scripting.traverser.IGNORE_POLLUTION = False
    if err.final_context is not None:
        print err.final_context.output()

    return err


def _do_real_test_raw(script, path="foo", versions=None, detected_type=None,
                      metadata=None, resources=None):
    """Perform a JS test using a non-mock bundler."""

    err = ErrorBundle()
    if detected_type:
        err.detected_type = detected_type
    err.supported_versions = versions or {}
    if metadata is not None:
        err.metadata = metadata
    if resources is not None:
        err.resources = resources

    validator.testcases.scripting.test_js_file(err, path, script, line=30)
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

