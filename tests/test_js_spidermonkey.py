import mock

from nose.tools import assert_raises, eq_

from .js_helper import _do_test_raw, _get_var

from validator import decorator
from validator.constants import SPIDERMONKEY_INSTALLATION
from validator.errorbundler import ErrorBundle
from validator.testcases import scripting
from validator.testcases.javascript.jsshell import JSShell, get_tree


def test_scripting_disabled():
    'Ensure that Spidermonkey is not run if it is set to be disabled.'

    err = ErrorBundle()
    err.save_resource('SPIDERMONKEY', None)
    assert scripting.test_js_file(err, 'abc def', 'foo bar') is None

    with mock.patch.object(scripting, 'SPIDERMONKEY_INSTALLATION', new=None):
        err = ErrorBundle()
        assert scripting.test_js_file(err, 'abc def', 'foo bar') is None


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


@mock.patch('subprocess.Popen')
def test_cleanup(Popen):
    """Test that the spidermonkey processes are terminated during cleanup."""

    # Make sure we don't already have a cached shell.
    JSShell.cleanup()
    eq_(JSShell.shells, {})
    assert not Popen.called

    process = mock.Mock()
    process.stdout.readline.return_value = '{}\n'
    Popen.return_value = process

    get_tree('hello();', shell=SPIDERMONKEY_INSTALLATION)

    eq_(Popen.call_count, 1)
    eq_(JSShell.shells.keys(), [SPIDERMONKEY_INSTALLATION])
    assert not process.terminate.called

    decorator.cleanup()

    assert process.terminate.called
    eq_(JSShell.shells, {})


@mock.patch('subprocess.Popen')
def test_cleanup_on_error(Popen):
    """Test that the cached shells are removed on IO error."""

    # Make sure we don't already have a cached shell.
    JSShell.cleanup()
    eq_(JSShell.shells, {})

    process = mock.Mock()
    process.stdout.readline.return_value = '{}'
    Popen.side_effect = lambda *args, **kw: process

    # Success, should have cached shell.
    get_tree('hello();', shell=SPIDERMONKEY_INSTALLATION)
    eq_(Popen.call_count, 1)

    eq_(JSShell.shells.keys(), [SPIDERMONKEY_INSTALLATION])
    assert not process.terminate.called

    # Read error. No cached shell.
    process.stdout.readline.side_effect = IOError

    with assert_raises(IOError):
        get_tree('hello();', shell=SPIDERMONKEY_INSTALLATION)

    # No new processes created, since we had a cached shell from last time.
    eq_(Popen.call_count, 1)
    assert process.stdin.write.called
    assert process.stdout.readline.called

    eq_(JSShell.shells, {})

    # Write error. No cached shell.
    process = mock.Mock()
    process.stdin.write.side_effect = IOError

    with assert_raises(IOError):
        get_tree('hello();', shell=SPIDERMONKEY_INSTALLATION)

    # Cached shell should have been removed in the last run. New
    # process should be created.
    eq_(Popen.call_count, 2)
    assert process.stdin.write.called
    assert not process.stdout.readline.called

    eq_(JSShell.shells, {})
