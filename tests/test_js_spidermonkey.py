import json
import subprocess
from js_helper import _do_test_raw
from validator.errorbundler import ErrorBundle
import validator.testcases.scripting as scripting
import validator.testcases.javascript.spidermonkey as spidermonkey
from validator.errorbundler import ErrorBundle


def test_scripting_disabled():
    "Ensures that Spidermonkey is not run if it is set to be disabled"

    err = ErrorBundle()
    err.save_resource("SPIDERMONKEY", None)
    assert scripting.test_js_file(err, "abc def", "foo bar") is None

    err = ErrorBundle()
    si = scripting.SPIDERMONKEY_INSTALLATION
    scripting.SPIDERMONKEY_INSTALLATION = None

    assert scripting.test_js_file(err, "abc def", "foo bar") is None

    scripting.SPIDERMONKEY_INSTALLATION = si


def test_scripting_snippet():
    "Asserts that JS snippets are treated equally"

    err = ErrorBundle()
    err.supported_versions = {}
    scripting.test_js_snippet(err, "alert(1 + 1 == 2)", "bar.zap")
    assert not err.failed()

    err = ErrorBundle()
    err.supported_versions = {}
    scripting.test_js_snippet(err, "eval('foo');", "bar.zap")
    assert err.failed()


def test_reflectparse_presence():
    "Tests that when Spidermonkey is too old, a proper error is produced"

    spidermonkey.subprocess = MockSubprocess()

    try:
        spidermonkey._get_tree("foo bar", "[path]")
    except RuntimeError as err:
        print str(err)
        assert (str(err) ==
            "Spidermonkey version too old; 1.8pre+ required; "
            "error='ReferenceError: Reflect is not defined'; "
            "spidermonkey='[path]'")
    except:
        raise

    spidermonkey.subprocess = subprocess


def test_compiletime_errors():
    "Tests that compile time errors don't break the validator"

    # Syntax error
    assert _do_test_raw("var x =;").failed()

    # Reference error
    assert _do_test_raw("x - y = 4;").failed()


class MockSubprocess(object):
    "A class to mock subprocess"

    def __init__(self):
        self.PIPE = True

    def Popen(self, command, shell, stderr, stdout):
        return MockSubprocessObject()


class MockSubprocessObject(object):
    "A class to mock a subprocess object and implement the communicate method"

    def communicate(self):
        data = json.dumps({"error": True,
                           "error_message": "ReferenceError: Reflect is not defined",
                           "line_number": 0})
        return data, ""


