import validator.testcases.themes as themes
from validator.errorbundler import ErrorBundle
from helper import _do_test


def test_theme_chrome_manifest():
    "Tests that a theme has a valid chrome manifest file."

    _do_test("tests/resources/themes/pass.jar",
             themes.test_theme_manifest,
             False)


def test_theme_bad_chrome_manifest():
    "Tests that a theme has an invalid chrome manifest file."

    _do_test("tests/resources/themes/fail.jar",
             themes.test_theme_manifest)


def test_no_chrome_manifest():
    "Tests that validation is skipped if there is no chrome manifest."

    assert themes.test_theme_manifest(ErrorBundle(), None) is None

