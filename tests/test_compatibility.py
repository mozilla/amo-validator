import validator.testcases.compatibility as compatibility
from validator.errorbundler import ErrorBundle

def test_compat_test():
    """Test that basic compatibility is supported"""

    err = ErrorBundle()
    err.save_resource("supported_versions",
                      {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                           ["5.0.x"]})

    compatibility.firefox_5_test(err, {}, None)
    assert err.notices

