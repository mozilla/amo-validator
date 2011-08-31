import validator.testcases.installrdf as installrdf
from validator.errorbundler import ErrorBundle
from validator.rdf import RDFParser
from validator.constants import *


def _test_value(value, test, failure=True):
    "Tests a value against a test."

    err = ErrorBundle()

    test(err, value)

    if failure:
        return err.failed()
    else:
        return not err.failed()


def test_pass_id():
    "Tests that valid IDs will be accepted."

    _test_value("{12345678-1234-1234-1234-123456789012}",
                installrdf._test_id,
                False)
    _test_value("abc@foo.bar",
                installrdf._test_id,
                False)
    _test_value("a+bc@foo.bar",
                installrdf._test_id,
                False)


def test_fail_id():
    "Tests that invalid IDs will not be accepted."

    _test_value("{1234567-1234-1234-1234-123456789012}",
                installrdf._test_id)
    _test_value("!@foo.bar",
                installrdf._test_id)


def test_pass_version():
    "Tests that valid versions will be accepted."

    _test_value("1.2.3.4",
                installrdf._test_version,
                False)
    _test_value("1a.2.3b+*.-_",
                installrdf._test_version,
                False)


def test_fail_version():
    "Tests that invalid versions will not be accepted."

    _test_value("2.0 alpha", installrdf._test_version)
    _test_value("whatever", installrdf._test_version)
    _test_value("123456789012345678901234567890123", installrdf._test_version)
    _test_value("1.2.3%", installrdf._test_version)


def test_pass_name():
    "Tests that valid names will be accepted."

    _test_value("Joe Schmoe's Feed Aggregator",
                installrdf._test_name,
                False)
    _test_value("Ozilla of the M",
                installrdf._test_name,
                False)


def test_fail_name():
    "Tests that invalid names will not be accepted."

    _test_value("Love of the Firefox", installrdf._test_name)
    _test_value("Mozilla Feed Aggregator", installrdf._test_name)


def _run_test(filename, failure=True, detected_type=0, listed=True,
              overrides=None):
    "Runs a test on an install.rdf file"

    return _run_test_raw(open(filename).read(), failure, detected_type,
                         listed, overrides)

def _run_test_raw(data, failure=True, detected_type=0, listed=True,
                  overrides=None):
    "Runs a test on an install.rdf snippet"

    data = data.strip()

    err = ErrorBundle()
    err.detected_type = detected_type
    err.save_resource("listed", listed)
    err.overrides = overrides

    parser = RDFParser(data)
    installrdf._test_rdf(err, parser)

    print err.print_summary(verbose=True)

    if failure: # pragma: no cover
        assert err.failed() or err.notices
    else:
        assert not err.failed() and not err.notices

    return err


def test_has_rdf():
    "Tests that tests won't be run if there's no install.rdf"

    err = ErrorBundle()

    assert installrdf.test_install_rdf_params(err, None) is None

    err.detected_type = 0
    err.save_resource("install_rdf", "test")
    err.save_resource("has_install_rdf", True)
    testrdf = installrdf._test_rdf
    installrdf._test_rdf = lambda x, y: y

    result = installrdf.test_install_rdf_params(err, None)
    installrdf._test_rdf = testrdf

    print result
    assert result == "test"

    return err


def test_passing():
    "Tests a passing install.rdf package."

    err = _run_test("tests/resources/installrdf/pass.rdf", False)
    assert not err.get_resource("unpack")


def test_unpack():
    "Tests that the unpack variable is ."

    err = _run_test("tests/resources/installrdf/unpack.rdf", False)
    assert err.get_resource("em:unpack") == "true"


def test_must_exist_once():
    "Tests that elements that must exist once only exist once."

    _run_test("tests/resources/installrdf/must_exist_once_missing.rdf")
    _run_test("tests/resources/installrdf/must_exist_once_extra.rdf")


def test_may_exist_once():
    "Tests that elements that may exist once only exist up to once."

    _run_test("tests/resources/installrdf/may_exist_once_missing.rdf",
              False)
    _run_test("tests/resources/installrdf/may_exist_once_extra.rdf")


def test_may_exist_once_theme():
    "Tests that elements that may exist once in themes."

    _run_test("tests/resources/installrdf/may_exist_once_theme.rdf",
              False,
              PACKAGE_THEME)
    _run_test("tests/resources/installrdf/may_exist_once_theme_fail.rdf",
              True,
              PACKAGE_THEME)
    _run_test("tests/resources/installrdf/may_exist_once_extra.rdf",
              True,
              PACKAGE_THEME)


def test_may_exist():
    "Tests that elements that may exist once only exist up to once."

    _run_test("tests/resources/installrdf/may_exist_missing.rdf",
              False)
    _run_test("tests/resources/installrdf/may_exist_extra.rdf", False)


def test_mustmay_exist():
    "Tests that elements that may exist once only exist up to once."

    # The first part of this is proven by test_must_exist_once

    _run_test("tests/resources/installrdf/mustmay_exist_extra.rdf",
              False)


def test_shouldnt_exist():
    "Tests that elements that shouldn't exist aren't there."

    _run_test("tests/resources/installrdf/shouldnt_exist.rdf")
    _run_test("tests/resources/installrdf/shouldnt_exist.rdf",
              listed=False,
              failure=False)


def test_obsolete():
    "Tests that obsolete elements are reported."

    err = _run_test("tests/resources/installrdf/obsolete.rdf")
    assert err.notices and not err.failed()


def test_overrides():
    """Test that overrides will work on the install.rdf file."""

    assert _run_test_raw(data="""
<?xml version="1.0"?>

<RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		xmlns:em="http://www.mozilla.org/2004/em-rdf#">

	<Description about="urn:mozilla:install-manifest">

	<em:id>bastatestapp1@basta.mozilla.com</em:id>
	<em:version>1.2.3.4</em:version>
    <!-- NOTE THAT NAME IS MISSING -->
	<em:targetApplication>
		<Description>
		<em:id>{ec8030f7-c20a-464f-9b0e-13a3a9e97384}</em:id>
		<em:minVersion>3.7a5pre</em:minVersion>
		<em:maxVersion>0.3</em:maxVersion>
		</Description>
	</em:targetApplication>

    </Description>

</RDF>
    """, failure=False, overrides={"ignore_empty_name": True})


def test_optionsType():
    """Test that the optionsType element works."""

    assert _run_test_raw(data="""
<?xml version="1.0"?>
<RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		xmlns:em="http://www.mozilla.org/2004/em-rdf#">
	<Description about="urn:mozilla:install-manifest">

	<em:id>bastatestapp1@basta.mozilla.com</em:id>
	<em:version>1.2.3.4</em:version>
    <em:name>foo bar</em:name>
	<em:targetApplication>
		<Description>
		<em:id>{ec8030f7-c20a-464f-9b0e-13a3a9e97384}</em:id>
		<em:minVersion>3.7a5pre</em:minVersion>
		<em:maxVersion>0.3</em:maxVersion>
		</Description>
	</em:targetApplication>

    <em:optionsType>2</em:optionsType>

    </Description>

</RDF>
    """, failure=False)


def test_optionsType_fail():
    """Test that the optionsType element fails with an invalid value."""

    assert _run_test_raw(data="""
<?xml version="1.0"?>
<RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		xmlns:em="http://www.mozilla.org/2004/em-rdf#">
	<Description about="urn:mozilla:install-manifest">

	<em:id>bastatestapp1@basta.mozilla.com</em:id>
	<em:version>1.2.3.4</em:version>
    <em:name>foo bar</em:name>
	<em:targetApplication>
		<Description>
		<em:id>{ec8030f7-c20a-464f-9b0e-13a3a9e97384}</em:id>
		<em:minVersion>3.7a5pre</em:minVersion>
		<em:maxVersion>0.3</em:maxVersion>
		</Description>
	</em:targetApplication>

    <em:optionsType>5</em:optionsType>

    </Description>

</RDF>
    """, failure=True)

