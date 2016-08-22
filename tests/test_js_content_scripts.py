import pytest

from js_helper import _do_test_raw


@pytest.mark.parametrize("test_input", [
    'foo.PageMod();',
    'foo.PageMod(null);',
    'foo.PageMod({});',
    'foo.PageMod(window);',
    'foo.PageMod({contentScript: null});',
    'foo.PageMod({contentScript: 4});',
])
def test_pagemod_noop(test_input):
    """
    Test that invalid conditions do not throw exceptions or messages when the
    PageMod function is used improperly.
    """
    assert not _do_test_raw(test_input).failed()


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
