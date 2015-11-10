from contextlib import contextmanager

from validator.errorbundler import ErrorBundle
from validator.testcases import packagejson


def test_no_tests_are_done_if_no_package_json():
    err = setup_err()
    packagejson.test_package_json_params(err)
    assert not err.failed()


def test_valid_package_json_is_valid():
    err = setup_err(valid_package_json())
    packagejson.test_package_json_params(err)
    assert not err.failed(), 'expected valid package.json to pass'


def test_name_cannot_have_trademarks():
    with setup_err_and_package() as (err, package):
        package['name'] = 'Mozilla Addon'
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected name with Mozilla to fail'


def test_name_is_required():
    with setup_err_and_package() as (err, package):
        del package['name']
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected name to be required'


def test_id_is_required_to_be_valid():
    with setup_err_and_package() as (err, package):
        package['id'] = 'not valid'
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected id to be invalid'


def test_id_is_required():
    with setup_err_and_package() as (err, package):
        del package['id']
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected id to be required'


def test_version_is_required():
    with setup_err_and_package() as (err, package):
        del package['version']
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected version to be required'


def test_version_must_be_valid():
    with setup_err_and_package() as (err, package):
        package['version'] = '2.5 beta'
    packagejson.test_package_json_params(err)
    assert err.failed(), 'expected invalid version to fail'


def valid_package_json():
    return {
        'id': 'my@awesome.addon',
        'name': 'My Awesome Addon',
        'version': '1.25',
    }


def setup_err(package_json=None, err=None):
    if err is None:
        err = ErrorBundle()
    if package_json is not None:
        err.save_resource('has_package_json', True)
        err.save_resource('package_json', package_json)
    return err


@contextmanager
def setup_err_and_package():
    package_json = valid_package_json()
    err = ErrorBundle()
    yield err, package_json
    setup_err(package_json, err)
