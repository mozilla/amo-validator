from js_helper import _do_test_raw, TestCase

def test_createElement():
    """Tests that createElement calls are filtered properly"""

    assert not _do_test_raw("""
    var x = "foo";
    x.createElement();
    x.createElement("foo");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElement("script");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElement(bar);
    """).failed()


def test_createElementNS():
    """Tests that createElementNS calls are filtered properly"""

    assert not _do_test_raw("""
    var x = "foo";
    x.createElementNS();
    x.createElementNS("foo");
    x.createElementNS("foo", "bar");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElementNS("foo", "script");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.createElementNS("foo", bar);
    """).failed()


def test_setAttribute():
    """Tests that setAttribute calls are blocked successfully"""

    assert not _do_test_raw("""
    var x = "foo";
    x.setAttribute();
    x.setAttribute("foo");
    x.setAttribute("foo", "bar");
    """).failed()

    assert _do_test_raw("""
    var x = "foo";
    x.setAttribute("onfoo", "bar");
    """).notices


def test_callexpression_argument_traversal():
    """
    This makes sure that unknown function calls still have their arguments
    traversed.
    """

    assert not _do_test_raw("""
    function foo(x){}
    foo({"bar":function(){
        bar();
    }});
    """).failed()

    assert _do_test_raw("""
    function foo(x){}
    foo({"bar":function(){
        eval("evil");
    }});
    """).failed()


def test_insertAdjacentHTML():
    """Test that insertAdjacentHTML works the same as innerHTML."""

    assert not _do_test_raw("""
    var x = foo();
    x.insertAdjacentHTML("foo bar", "<div></div>");
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.insertAdjacentHTML("foo bar", "<div onclick=\\"foo\\"></div>");
    """).failed()

    # Test without declaration
    assert _do_test_raw("""
    x.insertAdjacentHTML("foo bar", "<div onclick=\\"foo\\"></div>");
    """).failed()

    assert _do_test_raw("""
    var x = foo();
    x.insertAdjacentHTML("foo bar", "x" + y);
    """).failed()


class TestInstanceActions(TestCase):

    def test_openDialog_pass(self):
        """
        Test that `*.openDialog("<remote url>")` throws doesn't throw an error
        for chrome/local URIs.
        """
        self.run_script("""
        foo.openDialog("foo")
        foo.openDialog("chrome://foo/bar")
        """)
        self.assert_silent()

    def test_openDialog_flag_var(self):
        """
        Test that `*.openDialog(bar)` throws doesn't throw an error where `bar`
        is a dirty object.
        """
        self.run_script("""
        foo.openDialog(bar)
        """)
        self.assert_notices()

    def test_openDialog(self):
        """
        Test that `*.openDialog("<remote url>")` throws an error where
        <remote url> is a non-chrome, non-relative URL.
        """

        def test_uri(self, uri):
            self.setUp()
            self.setup_err()
            self.run_script('foo.openDialog("%s")' % uri)
            self.assert_failed(with_warnings=True)


        uris = ["http://foo/bar/",
                "https://foo/bar/",
                "ftp://foo/bar/",
                "data:asdf"]
        for uri in uris:
            yield test_uri, self, uri

