import validator.testcases.javascript.jstypes as jstypes


def test_jsarray_output():
    """Test that the output function for JSArray doesn't bork."""

    ja = jstypes.JSArray()
    ja.elements = [None, None]
    ja.output()  # Used to throw tracebacks.


def test_jsobject_output():
    """Test that the output function for JSObject doesn't bork."""

    jso = jstypes.JSObject()
    jso.data = {"first": None}
    jso.output()  # Used to throw tracebacks

