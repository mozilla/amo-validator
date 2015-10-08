from js_helper import _do_real_test_raw as _js


def test_nsIDOMFile_methods():
    """Test that deprecated DOM file methods do not cause an internal error."""

    _js("""
        var file = new File;
        file.getAsBinary();
    """)
