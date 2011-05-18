import json
from validator.validate import validate as validate
from validator.errorbundler import ErrorBundle
import validator.constants
import validator.testcases.targetapplication as targetapp

def test_validate():
    output = validate(path="tests/resources/packagelayout/theme.jar")
    j = json.loads(output)
    print j
    assert j["metadata"]["name"] == "name_value"

    output = validate(path="tests/resources/packagelayout/theme.jar",
                      format=None)
    assert isinstance(output, ErrorBundle)
    assert output.metadata["name"] == "name_value"
    assert output.get_resource("SPIDERMONKEY") == False

    output = validate(path="tests/resources/packagelayout/theme.jar",
                      spidermonkey="foospidermonkey",
                      format=None)
    assert output.get_resource("SPIDERMONKEY") == "foospidermonkey"
    assert output.determined
    assert output.get_resource("listed")

    output = validate(path="tests/resources/packagelayout/theme.jar",
                      determined=False,
                      format=None)
    assert not output.determined
    assert output.get_resource("listed")

    output = validate(path="tests/resources/packagelayout/theme.jar",
                      listed=False,
                      format=None)
    assert output.determined
    assert not output.get_resource("listed")

    output = validate(path="tests/resources/packagelayout/theme.jar",
                      overrides="foo",
                      format=None)
    assert output.overrides == "foo"

def test_app_versions():
    "Tests that the validate function properly loads app_versions.json"
    validate(path="tests/resources/junk.xpi",
             approved_applications="tests/resources/test_app_versions.json")
    print validator.constants.APPROVED_APPLICATIONS
    assert validator.constants.APPROVED_APPLICATIONS["1"]["name"] == "Foo App"

