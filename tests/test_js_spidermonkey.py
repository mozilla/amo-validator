import mock

from nose.tools import assert_raises, eq_

from .js_helper import _do_test_raw, _get_var

from validator import decorator
from validator.errorbundler import ErrorBundle
from validator.testcases import scripting
from validator.testcases.javascript.jsshell import JSShell, get_tree


def test_scripting_snippet():
    'Assert that JS snippets are treated equally.'

    err = ErrorBundle()
    err.supported_versions = {}
    scripting.test_js_snippet(err, 'alert(1 + 1 == 2)', 'bar.zap')
    assert not err.failed()

    err = ErrorBundle()
    err.supported_versions = {}
    scripting.test_js_snippet(err, "eval('foo');", 'bar.zap')
    assert err.failed()


def test_unicode_escapes():
    """Test that unicode/hex escapes are passed through to Spidermonkey."""

    result = _do_test_raw("var foo = '\\u263a\\u0027\\x27'")

    assert not result.failed()

    eq_(_get_var(result, 'foo'), u"\u263a''")


def patch_init(mock_):
    def __init__(self, *args, **kw):
        self.returncode = None
        self.stdin = mock_.stdin
        self.stdout = mock_.stdout
        self.terminate = mock_.terminate
    return __init__


@mock.patch('spidermonkey.Spidermonkey.__init__', autospec=True)
def test_cleanup(Popen):
    """Test that the spidermonkey processes are terminated during cleanup."""

    process = mock.MagicMock()
    Popen.side_effect = patch_init(process)

    # Make sure we don't already have a cached shell.
    JSShell.cleanup()
    assert JSShell.instance is None
    assert not Popen.called

    process.stdout.readline.return_value = '{}\n'

    get_tree('hello();')

    eq_(Popen.call_count, 1)
    # Clear the reference to `self` in the call history so it can be reaped.
    Popen.reset_mock()

    assert JSShell.instance
    assert not process.terminate.called

    decorator.cleanup()

    assert process.terminate.called
    assert JSShell.instance is None


@mock.patch('spidermonkey.Spidermonkey.__init__', autospec=True)
def test_cleanup_on_error(Popen):
    """Test that the cached shells are removed on IO error."""

    process = mock.MagicMock()
    process.stdout.readline.return_value = '{}'

    Popen.side_effect = patch_init(process)

    # Make sure we don't already have a cached shell.
    JSShell.cleanup()
    assert JSShell.instance is None

    # Success, should have cached shell.
    get_tree('hello();')
    eq_(Popen.call_count, 1)

    assert JSShell.instance
    assert not process.terminate.called

    # Write error. No cached shell.
    process.stdout.readline.reset_mock()
    process.stdin.write.side_effect = IOError

    with assert_raises(IOError):
        get_tree('hello();')

    # No new processes created, since we had a cached shell from last time.
    eq_(Popen.call_count, 1)
    assert process.stdin.write.called
    assert not process.stdout.readline.called

    # Read error. No cached shell.
    process.stdin.write.reset_mock()
    process.stdin.write.side_effect = None
    process.stdout.readline.side_effect = IOError

    with assert_raises(IOError):
        get_tree('hello();')

    assert JSShell.instance is None

    # Cached shell should have been removed in the last run. New
    # process should be created.
    eq_(Popen.call_count, 2)
    assert process.stdin.write.called
    assert process.stdout.readline.called

    assert JSShell.instance is None
