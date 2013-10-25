from mock import patch

from validator.compat import FX18_DEFINITION

from js_helper import _do_test_raw, TestCase


_DANGEROUS_STRINGS = ['"x" + y',
                      '"<div onclick=\\"foo\\"></div>"',
                      '"<a href=\\"javascript:alert();\\">"',
                      '"<script>"']


def test_innerHTML():
    """Tests that the dev can't define event handlers in innerHTML."""

    assert not _do_test_raw("""
    var x = foo();
    x.innerHTML = "<div></div>";
    """).failed()

    for pattern in _DANGEROUS_STRINGS:

        assert _do_test_raw("""
        var x = foo();
        x.innerHTML = %s;
        """ % pattern).failed(), pattern

        assert _do_test_raw("""
        x.innerHTML = %s;
        """ % pattern).failed(), pattern


def test_outerHTML():
    """Test that the dev can't define event handler in outerHTML."""

    assert not _do_test_raw("""
    var x = foo();
    x.outerHTML = "<div></div>";
    """).failed()

    for pattern in _DANGEROUS_STRINGS:

        assert _do_test_raw("""
        var x = foo();
        x.outerHTML = %s;
        """ % pattern).failed(), pattern

        assert _do_test_raw("""
        x.outerHTML = %s;
        """ % pattern).failed(), pattern


def test_document_write():
    """Test that the dev can't define event handler in outerHTML."""

    assert _do_test_raw("""
    document.write("<div></div>");
    """).failed()

    assert _do_test_raw("""
    document.writeln("<div></div>");
    """).failed()


def _mock_html_error(self, *args, **kwargs):
    self.err.error(("foo", "bar"),
                   "Does not pass validation.")

@patch('validator.testcases.markup.markuptester.MarkupParser.process',
       _mock_html_error)
def test_complex_innerHTML():
    """Tests that innerHTML can't be assigned an HTML chunk with bad code"""

    assert _do_test_raw("""
    var x = foo();
    x.innerHTML = "<b></b>";
    """).failed()


def test_function_return():
    """
    Test that the return value of a function is considered a dynamic value.
    """
    assert _do_test_raw("""x.innerHTML = foo();""").failed()


def test_on_event():
    """Tests that on* properties are not assigned strings."""

    assert not _do_test_raw("""
    var x = foo();
    x.fooclick = "bar";
    """).failed()

    assert not _do_test_raw("""
    var x = foo();
    x.onclick = function() {};
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.onclick = "bar";
    """).failed()


def test_on_event_null():
    """Null should not trigger on* events."""

    assert not _do_test_raw("""
    var x = foo(),
        y = null;
    x.onclick = y;
    """).failed()


class TestHandleEvent(TestCase):

    def test_on_event_handleEvent_pass(self):
        """
        Test that objects with `handleEvent` methods aren't flagged for
        versions of Gecko less than 18.
        """

        self.run_script("""
        foo.onclick = {handleEvent: function() {alert("bar");}};
        """)
        self.assert_failed(with_warnings=True)

    def test_on_event_handleEvent_fail(self):
        """
        Objects with `handleEvent` methods should be flagged as errors when add-ons
        target Gecko version 18.
        """

        self.setup_err(for_appversions=FX18_DEFINITION)

        self.run_script("""
        foo.onclick = {handleEvent: function() {alert("bar");}};
        """)
        self.assert_failed(with_warnings=True)

    def test_on_event_handleEvent_ignore(self):
        """
        Test that dirty objects don't trigger handleEvent errors.
        """

        self.setup_err(for_appversions=FX18_DEFINITION)

        self.run_script("""
        var dirty = this_creates_a_dirty_object();
        foo.onclick = dirty;
        """)
        self.assert_silent()



