from nose.tools import eq_

from js_helper import _do_test_raw


def test_pagemod_noop():
    """
    Test that invalid conditions do not throw exceptions or messages when the
    PageMod function is used improperly.
    """

    def wrap(script):
        assert not _do_test_raw(script).failed()

    yield wrap, 'foo.PageMod();'
    yield wrap, 'foo.PageMod(null);'
    yield wrap, 'foo.PageMod({});'
    yield wrap, 'foo.PageMod(window);'
    yield wrap, 'foo.PageMod({contentScript: null});'
    yield wrap, 'foo.PageMod({contentScript: 4});'


def test_pagemod_pass():
    """
    Test that invalid conditions do not throw exceptions or messages when the
    PageMod function is used with a valid JS script.
    """
    assert not _do_test_raw("foo.PageMod({contentScript: ''});").failed()
    assert not _do_test_raw("""
        foo.PageMod({contentScript: 'alert();'});
    """).failed()
    assert not _do_test_raw("""
        foo.PageMod({contentScript: "aler" + "t();"});
    """).failed()


def test_pagemod_fail():
    """
    Test that invalid conditions raise messages when the PageMod function is
    used with an unscrupulous JS script.
    """
    assert _do_test_raw("foo.PageMod({contentScript: 'eval();'});").failed()
    assert _do_test_raw("""
        foo.PageMod({contentScript: "ev" + "al();"});
    """).failed()
