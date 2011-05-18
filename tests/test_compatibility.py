import validator.constants
import validator.testcases.compatibility as compatibility
import validator.testcases.scripting as scripting
from validator.errorbundler import ErrorBundle


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

