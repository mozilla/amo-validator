import os
import validator.testcases.scripting

def test_banned_entity():
    "Tests that banned entities are disallowed"

    path = "tests/resources/bug_548645.js"
    script = open(path).read()

    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    print err.message_count
    assert err.message_count == 3

