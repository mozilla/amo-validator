from js_helper import _do_test

def test_no_dups():
    "Tests that errors are not duplicated."

    err = _do_test("tests/resources/javascript/dups.js")
    assert err.message_count == 6
    # 6 because prototypes are readonly in addition to accessing a member
    # of a dangerous object.

