from nose.tools import eq_

import validator.testcases.javascript.jstypes as jstypes
from js_helper import _do_test_raw


def test_jsarray_output():
    """Test that the output function for JSArray doesn't bork."""

    ja = jstypes.JSArray()
    ja.elements = [None, None]
    ja.output()  # Used to throw tracebacks.
    ja.get_literal_value()  # Also used to throw tracebacks.


def test_jsobject_output():
    """Test that the output function for JSObject doesn't bork."""

    jso = jstypes.JSObject()
    jso.data = {'first': None}
    jso.output()  # Used to throw tracebacks


def test_jsobject_recursion():
    """Test that circular references don't cause recursion errors."""

    jso = jstypes.JSObject()
    jso2 = jstypes.JSObject()

    jso.data = {'first': jstypes.JSWrapper(jso2)}
    jso2.data = {'second': jstypes.JSWrapper(jso)}

    print jso.output()
    assert '(recursion)' in jso.output()


def test_jsarray_recursion():
    """Test that circular references don't cause recursion errors."""

    ja = jstypes.JSArray()
    ja2 = jstypes.JSArray()

    ja.elements = [jstypes.JSWrapper(ja2)]
    ja2.elements = [jstypes.JSWrapper(ja)]

    print ja.output()
    assert '(recursion)' in ja.output()

    print ja.get_literal_value()
    assert '(recursion)' in ja.get_literal_value()


def test_jsliteral_regex():
    """
    Test that there aren't tracebacks from JSLiterals that perform raw binary
    operations.
    """
    assert not _do_test_raw("""
    var x = /foo/gi;
    var y = x + " ";
    var z = /bar/i + 0;
    """).failed()


def test_jsarray_contsructor():
    """
    Test for tracebacks that were caused by JSArray not calling it's parent's
    constructor.
    """
    assert not _do_test_raw("""
    var x = [];
    x.foo = "bar";
    x["zap"] = "foo";
    baz("zap" in x);
    """).failed()


def test_jsobject_computed_properties():
    """
    Tests that computed property names work as expected.
    """

    ID = ('testcases_javascript_instancetypes', 'set_on_event',
          'on*_str_assignment')

    err1 = _do_test_raw("""
        var foo = {};
        foo["onthing"] = "stuff";
    """)
    err2 = _do_test_raw("""
        var foo = {
            ["onthing"]: "stuff",
        };
    """)

    eq_(err1.warnings[0]['id'], ID)
    eq_(err2.warnings[0]['id'], ID)

    assert not _do_test_raw("""
        var foo = {
            [Symbol.iterator]: function* () {},
            ["foo" + bar]: "baz",
            [thing]: "quux",
        };
    """).failed()


def test_jsobject_get_wrap():
    """Test that JSObject always returns a JSWrapper."""

    x = jstypes.JSObject()
    x.data['foo'] = jstypes.JSLiteral('bar')

    out = x.get('foo')
    assert isinstance(out, jstypes.JSWrapper)
    eq_(out.get_literal_value(), 'bar')


def test_jsarray_get_wrap():
    """Test that JSArray always returns a JSWrapper."""

    x = jstypes.JSArray()
    x.elements = [None, jstypes.JSLiteral('bar')]

    out = x.get('1')
    assert isinstance(out, jstypes.JSWrapper)
    eq_(out.get_literal_value(), 'bar')
