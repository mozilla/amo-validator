import validator.constants
import validator.testcases.compatibility as compatibility
import validator.testcases.scripting as scripting
from validator.errorbundler import ErrorBundle


def test_compat_test():
    """Test that basic compatibility is supported"""

    err = ErrorBundle()
    err.save_resource("supported_versions",
                      {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                           ["5.0a2"]})

    compatibility.firefox_5_test(err, {}, None)
    print err.notices
    assert err.notices
    assert err.notices[0]["compatibility_type"] == "notice"


def test_versions_after():
    """
    Tests that the appropriate versions after the specified versions are
    returned.
    """

    av = validator.constants.APPROVED_APPLICATIONS

    new_versions = {"1": {"guid": "foo",
                          "versions": map(str, range(10))}}
    validator.constants.APPROVED_APPLICATIONS = new_versions

    assert compatibility.versions_after("foo", "8") == ["8", "9"]
    assert compatibility.versions_after("foo", "5") == ["5", "6", "7", "8",
                                                        "9"]

    validator.constants.APPROVED_APPLICATIONS = av


def test_navigator_language():
    """
    Test that 'navigator.language' is flagged as potentially incompatile with FX5.
    """

    err = ErrorBundle()

    flagged = "alert(navigator.language);"
    scripting.test_js_snippet(err, flagged, "foo")
    assert not err.failed()

    print err.print_summary()
    print err.get_resource("compat_references")

    compatibility.navigator_language(err, {}, None)
    assert err.failed()
    assert err.warnings[0]["compatibility_type"] == "error"

