import validator.testcases.javascript.jstypes as jstypes


def test_jsarray_output():
    """Test that the output function for JSArray doesn't bork."""

    ja = jstypes.JSArray()
    ja.elements = [None, None]
    ja.output()  # Used to throw tracebacks.

