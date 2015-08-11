import mock

from nose.tools import eq_

from validator import submain
from validator.errorbundler import ErrorBundle
from validator.constants import PACKAGE_ANY, PACKAGE_SEARCHPROV


@mock.patch('validator.submain.test_inner_package')
def test_package_pass(test_inner_package):
    'Tests the test_package function with simple data'

    err = ErrorBundle()
    with open('tests/resources/submain/install_rdf.xpi') as pkg:
        submain.test_package(err, pkg, pkg.name)

    assert not err.failed()
    assert err.get_resource('has_install_rdf')
    assert submain.test_inner_package.called


@mock.patch('validator.submain.test_inner_package')
def test_package_corrupt(test_inner_package):
    'Tests the test_package function fails with a non-zip'

    err = ErrorBundle()
    with open('tests/resources/junk.xpi') as pkg:
        submain.test_package(err, pkg, pkg.name)

    assert not test_inner_package.called
    assert err.failed()


@mock.patch('validator.submain.test_inner_package')
def test_package_corrupt_again(test_inner_package):
    'Tests the test_package function fails with a corrupt file'

    err = ErrorBundle()
    with open('tests/resources/corrupt.xpi') as pkg:
        submain.test_package(err, pkg, pkg.name)

    assert not test_inner_package.called
    assert err.failed()


@mock.patch('validator.submain.test_inner_package')
def test_package_extension_expectation(test_inner_package):
    'Tests the test_package function with an odd extension'

    err = ErrorBundle()
    with open('tests/resources/submain/install_rdf.jar') as pkg:
        submain.test_package(err, pkg, pkg.name, PACKAGE_ANY)

    assert submain.test_inner_package.called
    assert not err.failed()
    assert err.get_resource('has_install_rdf')


@mock.patch('validator.submain.test_inner_package')
def test_package_extension_bad_expectation(test_inner_package):
    'Tests the test_package function with an odd extension'

    err = ErrorBundle()
    with open('tests/resources/submain/install_rdf.jar') as pkg:
        submain.test_package(err, pkg, pkg.name, PACKAGE_SEARCHPROV)

    assert test_inner_package.called
    assert err.failed()
    eq_(err.errors[0]['id'], ('main', 'test_package', 'unexpected_type'))
