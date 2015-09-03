from .compat import get_compat_tests
from .generic import validate_file
from .javascript import validate_pref, validate_string  # noqa


def run_regex_tests(document, err, filename):
    """Run all of the regex-based JS tests."""

    validate_file(document, err=err, filename=filename)

    if err.for_appversions:
        tester = get_compat_tests(err)
        tester.test(document, err=err, filename=filename)
