import os
from validator.errorbundler import ErrorBundle
import validator.testcases.scripting as scripting

def test_valid():
    err = ErrorBundle(None, True)
    data = open("tests/resources/bug_590992_valid.js").read()
    scripting.test_js_file(err=err, filename="test", data=data)

    assert not err.failed()

def test_malicious():
    err = ErrorBundle(None, True)
    data = open("tests/resources/bug_590992_mal.js").read()
    scripting.test_js_file(err=err, filename="test", data=data)

    assert err.failed()


