import os

import validator.unicodehelper
import validator.testcases.scripting

# Originated from bug 626496

def _do_test(path):
    "Performs a test on a JS file"
    script = validator.unicodehelper.decode(open(path, "rb").read())
    print script.encode("ascii", "backslashreplace")

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    print err.ids

    return err

def test_controlchars_ascii_ok():
    """Tests that multi-byte characters are decoded properly (utf-8)"""

    errs = _do_test("tests/resources/controlchars/controlchars_ascii_ok.js")
    assert len(errs.ids) == 0

def test_controlchars_ascii_warn():
    """Tests that multi-byte characters are decoded properly (utf-8)
		but remaining non ascii characters raise warnings"""

    errs = _do_test("tests/resources/controlchars/controlchars_ascii_warn.js")
    assert len(errs.ids) == 1 and errs.ids[0][2] == "syntax_error"

def test_controlchars_utf8_ok():
    """Tests that multi-byte characters are decoded properly (utf-8)"""

    errs = _do_test("tests/resources/controlchars/controlchars_utf-8_ok.js")
    assert len(errs.ids) == 0

def test_controlchars_utf8_warn():
    """Tests that multi-byte characters are decoded properly (utf-8)
		but remaining non ascii characters raise warnings"""

    errs = _do_test("tests/resources/controlchars/controlchars_utf-8_warn.js")
    assert len(errs.ids) == 1 and errs.ids[0][2] == "syntax_error"

