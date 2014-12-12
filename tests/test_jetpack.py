from nose.tools import eq_

import hashlib

from js_helper import _do_real_test_raw as _js_test, _test_xpi
from tests.test_frameworks import (MockXPI, accepted_version,
                                   assert_framework_files)
from validator.errorbundler import ErrorBundle
from validator.testcases.markup.markuptester import MarkupParser
from validator.xpi import XPIManager


# These files are a subset of the framework tests which are specific
# to Jetpack. They're currently split into a separate file since
# they're considerably more comprehensive than any other framework
# tests, and mostly predate the current generalized tests.

with open("tests/resources/bootstrap.js") as bootstrap_file:
    bootstrap = bootstrap_file.read()
with open("tests/resources/bootstrap-jpm.js") as bootstrap_file:
    bootstrap_jpm = bootstrap_file.read()


def _do_test(xpi_package, allow_old_sdk=True):
    err = _test_xpi(xpi_package)

    if allow_old_sdk:
        err_id = ("testcases_frameworks", "validate_jetpack_cfx",
                  "outdated_version")

        err.warnings = [e for e in err.warnings if e["id"] != err_id]

    print err.print_summary(verbose=True)
    return err


def test_not_jetpack():
    """Test that add-ons which do not match the Jetpack pattern are ignored."""

    err = _do_test(MockXPI({"foo": True, "bar": True}))
    eq_(err.errors, [])
    eq_(err.warnings, [])
    eq_(err.notices, [])
    eq_(err.metadata.get('is_jetpack', False), False)


def test_package_json_jetpack():
    """Test that add-ons with the new package.json are treated as jetpack."""
    err = _do_test(MockXPI({"bootstrap.js": bootstrap_jpm,
                            "package.json": "{}"}))
    eq_(err.errors, [])
    eq_(err.warnings, [])
    eq_(err.notices, [])
    eq_(err.metadata.get('is_jetpack'), True)


def test_bad_harnessoptions():
    """Test that a malformed harness-options.json file is warned against."""

    err = _do_test(MockXPI({"bootstrap.js": True,
                            "components/harness.js": True,
                            "harness-options.json": "foo bar"}))
    assert err.failed()
    assert err.errors
    assert err.errors[0]["id"][-1] == "invalid_metadata"


def test_pass_jetpack():
    """Test that a minimalistic Jetpack setup will pass."""

    harnessoptions = {"sdkVersion": "1.7",
                      "jetpackID": "",
                      "manifest": {}}

    with accepted_version("frameworks", "jetpack", "versions", "1.7"):
        err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                                "harness-options.json": harnessoptions}))

    eq_(err.notices, [])
    eq_(err.warnings, [])
    eq_(err.errors, [])

    assert err.metadata.get("is_jetpack")

    assert_framework_files(err, ["bootstrap.js"])


def test_package_json_pass_jetpack():
    """Test that a minimalistic package.json Jetpack setup will pass."""

    err = _do_test(MockXPI({"bootstrap.js": bootstrap_jpm,
                            "package.json": "{}"}))

    assert not err.failed()
    assert err.metadata.get("is_jetpack")

    assert_framework_files(err, ["bootstrap.js"])


def test_package_json_different_bootstrap():
    """Test that a minimalistic package.json Jetpack setup will pass."""

    err = _do_test(MockXPI({"bootstrap.js": bootstrap_jpm,
                            "package.json": "{}"}))
    assert not err.failed()
    assert err.metadata.get("is_jetpack")

    assert_framework_files(err, ["bootstrap.js"])


def test_missing_elements():
    """Test that missing elements in harness-options will fail."""

    harnessoptions = {"sdkVersion": "1.7",
                      "jetpackID": ""}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "harness-options.json": harnessoptions}))
    assert err.failed()


def test_skip_safe_files():
    """
    Tests that errors aren't triggered by the presence of certain files.
    I'm not actually certain what the purpose of this test is, but the previous
    docstring was for a different test.
    """

    harnessoptions = {"sdkVersion": "1.7",
                      "jetpackID": "",
                      "manifest": {}}

    with accepted_version("frameworks", "jetpack", "versions", "1.7"):
        err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                                "harness-options.json": harnessoptions,
                                "foo.png": True,
                                "bar.JpG": True,
                                "safe.GIF": True,
                                "icon.ico": True}))
    assert not err.failed()


def test_pass_manifest_elements():
    """Test that proper elements in harness-options will pass."""

    bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "jetpackID": "foobar",
            "sdkVersion": "1.7",
            "manifest": {
                "bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "sectionName": "lib",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    with accepted_version("frameworks", "jetpack", "versions", "1.7"):
        err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                                "harness-options.json": harnessoptions,
                                "resources/bootstrap.js": bootstrap}))
    assert not err.failed()
    assert "jetpack_loaded_modules" in err.metadata
    eq_(err.metadata["jetpack_loaded_modules"],
        ["addon-kit-lib/drawing.js"])
    assert_framework_files(err, ["bootstrap.js"])

    if False:
        # Might want to implement an equivalent for this. Might not.
        # This information is already gleanable by checking both
        # "identified_files" and "framework_files".
        assert "jetpack_unknown_files" in err.metadata
        assert not err.metadata["jetpack_unknown_files"]


def test_ok_resource():
    """Test that resource:// URIs aren't flagged."""

    bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "jetpackID": "foobar",
            "sdkVersion": "1.7",
            "manifest": {
                "resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "sectionName": "lib",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    with accepted_version("frameworks", "jetpack", "versions", "1.7"):
        err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                                "resources/bootstrap.js": bootstrap,
                                "harness-options.json": harnessoptions}))
    assert not err.failed()


def test_bad_resource():
    """Test for failure on non-resource:// modules."""

    bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "1.7",
            "jetpackID": "foobar",
            "manifest":
                {"http://foo.com/bar/bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "sectionName": "lib",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json": harnessoptions}))
    assert err.failed()


def test_missing_manifest_elements():
    """Test that missing manifest elements in harness-options will fail."""

    bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "1.7",
            "jetpackID": "foobar",
            "manifest":
                {"resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json": harnessoptions}))
    assert err.failed()


def test_mismatched_hash():
    """
    Test that failure occurs when the actual file hash doesn't match the hash
    provided by harness-options.js.
    """

    harnessoptions = {
            "sdkVersion": "1.7",
            "jetpackID": "foobar",
            "manifest":
                {"resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "moduleName": "drawing",
                     "jsSHA256": "",
                     "docsSHA256": ""}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json": harnessoptions}))
    assert err.failed()


def test_mismatched_db_hash():
    """
    Test that failure occurs when the hash of a file doesn't exist in the
    Jetpack known file database.
    """

    # Break the hash with this.
    bootstrap = "function() {}; %s" % globals()["bootstrap"]
    bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "1.7",
            "jetpackID": "foobar",
            "manifest":
                {"resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "moduleName": "drawing",
                     "sectionName": "lib",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json": harnessoptions}))
    assert err.failed()
    assert (("testcases_frameworks", "unknown_file") in
            (e["id"] for e in err.errors))

    assert "jetpack_loaded_modules" not in err.metadata

    # There is currently no analog for this. Restore if we decide to
    # create one.
    # assert "jetpack_unknown_files" in err.metadata

    identified_files = err.metadata.get("identified_files")
    framework_files = err.metadata.get("framework_files")
    eq_(identified_files, {})
    eq_(framework_files,
        ["bootstrap.js",
         "harness-options.json"])


def test_mismatched_module_version():
    """
    Tests that add-ons using modules from a version of the SDK
    other than the version they claim.
    """

    with accepted_version("frameworks", "jetpack", "versions", "1.8.1"):
        xpi = XPIManager("tests/resources/jetpack/"
                         "jetpack-1.8-pretending-1.8.1.xpi")
        err = _do_test(xpi)

    assert err.failed()
    assert (("testcases_frameworks", "incorrect_file_version") in
            (e["id"] for e in err.errors))


def test_new_module_location_spec():
    """
    Tests that we don't fail for missing modules in add-ons generated with
    newer versions of the SDK.
    """

    xpi = XPIManager("tests/resources/jetpack/jetpack-1.14.xpi")
    err = _do_test(xpi)

    assert not any(w["id"][2] == "missing_jetpack_module"
                   for w in err.warnings)


def test_components_flagged():
    """Test that `Components` is flagged in Jetpack."""

    js = """
    var x = Components.services.foo.bar;
    """
    assert not _js_test(js).failed()
    assert _js_test(js, jetpack=True).failed()


def test_absolute_uris_in_js():
    """
    Test that a warning is thrown for absolute URIs within JS files.
    """

    bad_js = 'alert("resource://foo-data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err =_js_test(bad_js, jetpack=True)
    assert err.failed()
    assert err.compat_summary["errors"]

    # Test that literals are inspected even if they're the result of an
    # operation.
    bad_js = 'alert("resou" + "rce://foo-" + "data/bar/zap.png");'
    assert not _js_test(bad_js).failed()
    err =_js_test(bad_js, jetpack=True)
    assert err.failed()
    assert err.compat_summary["errors"]


def test_observer_service_flagged():
    assert _js_test("""
    var {Ci} = require("chrome");
    thing.QueryInterface(Ci.nsIObserverService);
    """, jetpack=True).failed()

    assert not _js_test("""
    thing.QueryInterface(Ci.nsIObserverService);
    """).failed()


def test_absolute_uris_in_markup():
    """
    Test that a warning is thrown for absolute URIs within markup files.
    """

    err = ErrorBundle()
    bad_html = '<foo><bar src="resource://foo-data/bar/zap.png" /></foo>'

    parser = MarkupParser(err)
    parser.process("foo.html", bad_html, "html")
    assert not err.failed()

    err.metadata["is_jetpack"] = True
    parser = MarkupParser(err)
    parser.process("foo.html", bad_html, "html")
    assert err.failed()
    assert err.compat_summary["errors"]


def test_bad_sdkversion():
    """Test that a deprecated SDK version is not used."""

    harnessoptions = {"sdkVersion": "1.4",
                      "jetpackID": "",
                      "manifest": {}}

    with open("jetpack/addon-sdk/packages/test-harness/lib/"
                  "harness.js") as harness_file:
        harness = harness_file.read()

    with accepted_version("frameworks", "jetpack", "versions", "1.4"):
        err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                                "components/harness.js": harness,
                                "harness-options.json": harnessoptions}))
    assert err.failed() and err.errors


def test_outdated_sdkversion():
    """
    Tests that add-ons using a version other than the latest release
    are warned against, but module hashes are still recognized.
    """

    xpi = XPIManager("tests/resources/jetpack/jetpack-1.8-outdated.xpi")
    with accepted_version("frameworks", "jetpack", "versions", "1.8"):
        err = _do_test(xpi, allow_old_sdk=False)

    assert err.failed()
    # Make sure we don't have any version mismatch warnings
    eq_(err.errors, [])
    eq_(len(err.warnings), 1)
    eq_(err.warnings[0]["id"][2], "outdated_version")
