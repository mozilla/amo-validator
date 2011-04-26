import json
from StringIO import StringIO

import validator.testcases.targetapplication as targetapp
from validator.constants import *
from validator.errorbundler import ErrorBundle
from validator.rdf import RDFParser
from helper import _do_test

targetapp.APPROVED_APPLICATIONS = \
        json.load(open("validator/app_versions.json"))

def _do_test_raw(rdf):
    err = ErrorBundle()
    rdf = RDFParser(StringIO(rdf.strip()))
    err.save_resource("has_install_rdf", True)
    err.save_resource("install_rdf", rdf)

    targetapp.test_targetedapplications(err)
    return err

def test_valid_targetapps():
    """Tests that the install.rdf contains only valid entries for
    target applications."""

    print targetapp.APPROVED_APPLICATIONS

    results = _do_test("tests/resources/targetapplication/pass.xpi",
                       targetapp.test_targetedapplications,
                       False,
                       True)
    print results.get_resource("supports")
    supports = results.get_resource("supports")
    assert "firefox" in supports and "mozilla" in supports
    assert len(supports) == 2

def test_bad_min_max():
    """Tests that the lower/upper-bound version number for a
    targetApplication entry is indeed a valid version number"""

    _do_test("tests/resources/targetapplication/bad_min.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

    _do_test("tests/resources/targetapplication/bad_max.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

def test_bad_order():
    """Tests that the min and max versions are ordered correctly such
    that the earlier version is the min and vice-versa."""

    _do_test("tests/resources/targetapplication/bad_order.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

def test_dup_targets():
    """Tests that there are no duplicate targetAppication elements."""

    _do_test("tests/resources/targetapplication/dup_targapp.xpi",
             targetapp.test_targetedapplications,
             True,
             True)

def test_has_installrdfs():
    """Tests that install.rdf files are present."""

    err = ErrorBundle(None, True)

    # Test package to make sure has_install_rdf is set to True.
    assert targetapp.test_targetedapplications(err, {}, None) is None

def test_is_ff4():
    """Tests a passing install.rdf package for whether it's built for
    Firefox 4. This doesn't pass or fail a package, but it is used for
    other tests in other modules in higher tiers."""

    results = _do_test("tests/resources/targetapplication/ff4.xpi",
                       targetapp.test_targetedapplications,
                       False,
                       True)

    assert results.get_resource("ff4")
    assert results.get_resource("supports")
    assert "firefox" in results.get_resource("supports")


def test_no_supported_mozilla_apps():
    """
    Tests that at least one supported Mozilla app is listed as a target
    application.
    """

    assert not _do_test_raw("""
    <?xml version="1.0"?>
    <RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:em="http://www.mozilla.org/2004/em-rdf#">
        <Description about="urn:mozilla:install-manifest">
            <em:targetApplication>
                <Description> <!-- Firefox -->
                    <em:id>{ec8030f7-c20a-464f-9b0e-13a3a9e97384}</em:id>
                    <em:minVersion>1.5</em:minVersion>
                    <em:maxVersion>3.0.*</em:maxVersion>
                </Description>
            </em:targetApplication>
        </Description>
    </RDF>
    """).failed()

    assert not _do_test_raw("""
    <?xml version="1.0"?>
    <RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:em="http://www.mozilla.org/2004/em-rdf#">
        <Description about="urn:mozilla:install-manifest">
            <em:targetApplication>
                <Description> <!-- Something else -->
                    <em:id>Blah blah blah</em:id>
                    <em:minVersion>1.2.3</em:minVersion>
                    <em:maxVersion>4.5.6</em:maxVersion>
                </Description>
            </em:targetApplication>
            <em:targetApplication>
                <Description> <!-- Firefox -->
                    <em:id>{ec8030f7-c20a-464f-9b0e-13a3a9e97384}</em:id>
                    <em:minVersion>1.5</em:minVersion>
                    <em:maxVersion>3.0.*</em:maxVersion>
                </Description>
            </em:targetApplication>
        </Description>
    </RDF>
    """).failed()

    assert _do_test_raw("""
    <?xml version="1.0"?>
    <RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:em="http://www.mozilla.org/2004/em-rdf#">
        <Description about="urn:mozilla:install-manifest">
            <em:targetApplication>
                <Description> <!-- Something else -->
                    <em:id>Blah blah blah</em:id>
                    <em:minVersion>1.2.3</em:minVersion>
                    <em:maxVersion>4.5.6</em:maxVersion>
                </Description>
            </em:targetApplication>
            <em:targetApplication>
                <Description> <!-- More junk -->
                    <em:id>More junk</em:id>
                    <em:minVersion>9.8.7</em:minVersion>
                    <em:maxVersion>6.5.4</em:maxVersion>
                </Description>
            </em:targetApplication>
        </Description>
    </RDF>
    """).failed()

