from validator.errorbundler import ErrorBundle
from validator.json_parser import ManifestJsonParser
from validator.testcases import manifestjson


def test_no_tests_are_done_if_no_manifest_json():
    err = ErrorBundle()
    manifestjson.test_manifest_json_params(err)
    assert not err.failed()


def test_valid_manifest_json_is_valid():
    err = setup_err()
    manifestjson.test_manifest_json_params(err)
    assert not err.failed(), 'expected valid manifest.json to pass'


def test_name_cannot_have_trademarks():
    err = setup_err()
    err.get_resource('manifest_json').data['name'] = 'Mozilla Addon'
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected name with Mozilla to fail'


def test_name_is_required():
    err = setup_err()
    del err.get_resource('manifest_json').data['name']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected name to be required'


def test_id_is_required_to_be_valid():
    err = setup_err()
    err.get_resource('manifest_json').data['applications']['gecko']['id'] = (
        'not valid')
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected id to be invalid'


def test_id_is_required():
    err = setup_err()
    del err.get_resource('manifest_json').data['applications']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected id to be required'


def test_version_is_required():
    err = setup_err()
    del err.get_resource('manifest_json').data['version']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected version to be required'


def test_version_must_be_valid():
    err = setup_err()
    err.get_resource('manifest_json').data['version'] = '2.5 beta'
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected invalid version to fail'


def setup_err():
    err = ErrorBundle()
    manifest_json = """{
        "name": "My Awesome Addon",
        "version": "1.25",

        "applications": {
            "gecko": {
                "id": "my@awesome.addon"
            }
        }
    }"""
    err.save_resource('has_manifest_json', True)
    err.save_resource('manifest_json', ManifestJsonParser(err, manifest_json))
    return err
