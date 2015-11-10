from contextlib import contextmanager

from validator.errorbundler import ErrorBundle
from validator.testcases import manifestjson


def test_no_tests_are_done_if_no_manifest_json():
    err = setup_err()
    manifestjson.test_manifest_json_params(err)
    assert not err.failed()


def test_valid_manifest_json_is_valid():
    err = setup_err(valid_manifest_json())
    manifestjson.test_manifest_json_params(err)
    assert not err.failed(), 'expected valid manifest.json to pass'


def test_name_cannot_have_trademarks():
    with setup_err_and_manifest() as (err, manifest):
        manifest['name'] = 'Mozilla Addon'
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected name with Mozilla to fail'


def test_name_is_required():
    with setup_err_and_manifest() as (err, manifest):
        del manifest['name']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected name to be required'


def test_id_is_required_to_be_valid():
    with setup_err_and_manifest() as (err, manifest):
        manifest['applications']['gecko']['id'] = 'not valid'
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected id to be invalid'


def test_id_is_required():
    with setup_err_and_manifest() as (err, manifest):
        del manifest['applications']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected id to be required'


def test_version_is_required():
    with setup_err_and_manifest() as (err, manifest):
        del manifest['version']
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected version to be required'


def test_version_must_be_valid():
    with setup_err_and_manifest() as (err, manifest):
        manifest['version'] = '2.5 beta'
    manifestjson.test_manifest_json_params(err)
    assert err.failed(), 'expected invalid version to fail'


def valid_manifest_json():
    return {
        "name": "My Awesome Addon",
        "version": "1.25",

        "applications": {
            "gecko": {
                "id": "my@awesome.addon"
            }
        }
    }


def setup_err(manifest_json=None, err=None):
    if err is None:
        err = ErrorBundle()
    if manifest_json is not None:
        err.save_resource('has_manifest_json', True)
        err.save_resource('manifest_json', manifest_json)
    return err


@contextmanager
def setup_err_and_manifest():
    manifest_json = valid_manifest_json()
    err = ErrorBundle()
    yield err, manifest_json
    setup_err(manifest_json, err)
