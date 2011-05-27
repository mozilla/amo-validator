import validator.submain as submain
from validator.errorbundler import ErrorBundle
from validator.constants import *


def test_package_pass():
    "Tests the test_package function with simple data"

    tip = submain.test_inner_package
    submain.test_inner_package = lambda x, y, z, for_appversions: "success"

    name = "tests/resources/submain/install_rdf.xpi"
    pack = open(name)
    err = ErrorBundle(None, True)

    result = submain.test_package(err, pack, name)

    pack.close()

    submain.test_inner_package = tip

    assert not err.failed()
    assert err.get_resource("has_install_rdf")
    assert result == "success"


def test_package_corrupt():
    "Tests the test_package function fails with a non-zip"

    tip = submain.test_inner_package
    submain.test_inner_package = lambda x, y, z, for_appversions: "success"

    name = "tests/resources/junk.xpi"
    err = ErrorBundle(None, True)

    result = submain.test_package(err, name, name)
    submain.test_inner_package = tip

    err.print_summary(True);
    assert err.failed()


def test_package_corrupt():
    "Tests the test_package function fails with a corrupt file"

    tip = submain.test_inner_package
    submain.test_inner_package = lambda x, y, z, for_appversions: "success"

    name = "tests/resources/corrupt.xpi"
    err = ErrorBundle(None, True)

    result = submain.test_package(err, name, name)
    submain.test_inner_package = tip

    err.print_summary(True);
    assert err.failed()


def test_package_extension_expectation():
    "Tests the test_package function with an odd extension"

    tip = submain.test_inner_package
    submain.test_inner_package = lambda x, y, z, for_appversions: "success"

    name = "tests/resources/submain/install_rdf.jar"
    err = ErrorBundle(None, True)

    result = submain.test_package(err, name, name, PACKAGE_ANY)

    submain.test_inner_package = tip

    assert not err.failed()
    assert err.get_resource("has_install_rdf")
    assert result == "success"


def test_package_extension_bad_expectation():
    "Tests the test_package function with an odd extension"

    tip = submain.test_inner_package
    submain.test_inner_package = lambda x, y, z, for_appversions: "success"

    name = "tests/resources/submain/install_rdf.jar"
    err = ErrorBundle(None, True)

    result = submain.test_package(err, name, name, PACKAGE_SEARCHPROV)

    submain.test_inner_package = tip

    assert err.failed()

