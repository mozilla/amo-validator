import json
import validator.testcases.javascript.spidermonkey as spidermonkey


def test_reflectparse_presence():
    "Tests that when Spidermonkey is too old, a proper error is produced"

    sp = spidermonkey.subprocess
    spidermonkey.subprocess = MockSubprocess()

    try:
        spidermonkey._get_tree("foo bar", "[path]")
    except RuntimeError as err:
        print str(err)
        assert str(err) == \
            "Spidermonkey version too old; " \
            "1.8pre+ required; error='ReferenceError: [errmsg]'; " \
            "spidermonkey='[path]'"
    except:
        raise

    spidermonkey.subprocess = sp


class MockSubprocess(object):
    "A class to mock subprocess"

    def __init__(self):
        self.PIPE = True

    def Popen(self, command, shell, stderr, stdout):
        return MockSubprocessObject()


class MockSubprocessObject(object):
    "A class to mock a subprocess object and implement the communicate method"

    def communicate(self):
        data = json.dumps({"error": True,
                           "error_message": "ReferenceError: [errmsg]"})
        return data, ""


