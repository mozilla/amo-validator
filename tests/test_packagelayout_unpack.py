from validator.errorbundler import ErrorBundle
from validator.constants import *
import validator.testcases.packagelayout as packagelayout
from helper import MockXPI


def _do_test(unpack=False, contents=None, set_type=0, is_ff4=False):
    "Runs the tests. Handy as hell."

    if not contents:
        contents = []

    err = ErrorBundle(None, True)
    if set_type:
        err.set_type(set_type)
    err.save_resource("em:unpack", unpack)
    err.save_resource("ff4", is_ff4)
    packagelayout.test_emunpack(err,
                                MockXPI(dict(zip(contents,
                                                 [True for c in contents]))))
    return err


def test_no_unpack():
    "Tests that packages for non-FF4 + no content + PACKAGE_ANY passes."

    assert not _do_test().failed()


def test_unpack_ff4():
    "Tests that if FF4 is not targeted, it should pass if unpack istrue."

    assert not _do_test(unpack="true",
                        contents=("foo.jar", ),
                        is_ff4=True).failed()


def test_no_unpack_ff4():
    "When FF4 is not supported and unpack is untrue, JARs should throw errors."

    assert not _do_test(contents=("foo.jar", ),
                        is_ff4=False).failed()


def test_no_unpack_dict():
    "When unpack is false/unset, it should always fail for dictionaries."

    assert _do_test(set_type=PACKAGE_DICTIONARY).failed()


def test_no_unpacked_ico():
    "Packages containing ICO files and unpack is unset/false should fail."

    assert _do_test(contents=("chrome/icons/default/foo.png", )).failed()


def test_no_unpacked_exec_safe():
    """Packages containing executable files outside the /components/ directory
    and where unpack is unset/false should NOT fail."""

    assert not _do_test(contents=("foo.exe", )).failed()


def test_no_unpacked_exec():
    """Packages containing executable files in the /components/ directory and
    where unpack is unset/false should fail."""

    assert _do_test(contents=("components/foo.exe", )).failed()

