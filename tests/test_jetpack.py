from nose.tools import eq_

import hashlib
import json
import nose

from js_helper import _do_real_test_raw as _js_test
from validator.testcases.markup.markuptester import MarkupParser
import validator.testcases.jetpack as jetpack
from validator.errorbundler import ErrorBundle

def _do_test(xpi_package):

    err = ErrorBundle()
    jetpack.inspect_jetpack(err, xpi_package)
    return err

class MockXPI:

    def __init__(self, resources):
        self.resources = resources

    def read(self, name):
        if isinstance(self.resources[name], bool):
            return ""
        return self.resources[name]

    def __iter__(self):
        for name in self.resources.keys():
            yield name

    def __contains__(self, name):
        return name in self.resources


def test_not_jetpack():
    """Test that add-ons which do not match the Jetpack pattern are ignored."""

    err = _do_test(MockXPI({"foo": True, "bar": True}))
    assert not err.errors
    assert not err.warnings
    assert not err.notices
    eq_(err.metadata.get('is_jetpack', False), False)


def test_bad_harnessoptions():
    """Test that a malformed harness-options.json file is warned against."""

    err = _do_test(MockXPI({"bootstrap.js": True,
                            "components/harness.js": True,
                            "harness-options.json": "foo bar"}))
    assert err.failed()
    assert err.warnings
    print err.warnings
    assert err.warnings[0]["id"][-1] == "bad_harness-options.json"


def test_pass_jetpack():
    """Test that a minimalistic Jetpack setup will pass."""

    harnessoptions = {"sdkVersion": "foo",
                      "jetpackID": "",
                      "manifest": {}}

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
    with open("jetpack/addon-sdk/packages/test-harness/lib/"
                  "harness.js") as harness_file:
        harness = harness_file.read()
    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "components/harness.js": harness,
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert "is_jetpack" in err.metadata and err.metadata["is_jetpack"]

    # Test that all files are marked as pretested.
    pretested_files = err.get_resource("pretested_files")
    assert pretested_files
    assert "bootstrap.js" in pretested_files

    # Even though harness.js is no longer in Jetpack 1.4+ add-ons, we should
    # make sure that we don't start throwing errors for it for older Jetpack
    # add-ons.
    assert "components/harness.js" in pretested_files


def test_missing_elements():
    """Test that missing elements in harness-options will fail."""

    harnessoptions = {"sdkVersion": "foo",
                      "jetpackID": ""}

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    assert err.failed()


def test_skip_safe_files():
    """Test that missing elements in harness-options will fail."""

    harnessoptions = {"sdkVersion": "foo",
                      "jetpackID": "",
                      "manifest": {}}

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "harness-options.json":
                                json.dumps(harnessoptions),
                            "foo.png": True,
                            "bar.JpG": True,
                            "safe.GIF": True,
                            "icon.ico": True,
                            "foo/.DS_Store": True}))
    assert not err.failed()


def test_pass_manifest_elements():
    """Test that proper elements in harness-options will pass."""

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "jetpackID": "foobar",
            "sdkVersion": "foo",
            "manifest": {
                "bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "sectionName": "lib",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "harness-options.json":
                                json.dumps(harnessoptions),
                            "resources/bootstrap.js": bootstrap}))
    print err.print_summary(verbose=True)
    assert not err.failed()
    assert "jetpack_loaded_modules" in err.metadata
    nose.tools.eq_(err.metadata["jetpack_loaded_modules"],
                   ["addon-kit-lib/drawing.js"])
    assert "jetpack_identified_files" in err.metadata
    assert "bootstrap.js" in err.metadata["jetpack_identified_files"]

    assert "jetpack_unknown_files" in err.metadata
    assert not err.metadata["jetpack_unknown_files"]


def test_ok_resource():
    """Test that resource:// URIs aren't flagged."""

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "jetpackID": "foobar",
            "sdkVersion": "foo",
            "manifest": {
                "resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "sectionName": "lib",
                     "moduleName": "drawing",
                     "jsSHA256": bootstrap_hash,
                     "docsSHA256": bootstrap_hash}}}

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()


def test_bad_resource():
    """Test for failure on non-resource:// modules."""

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "foo",
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
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_missing_manifest_elements():
    """Test that missing manifest elements in harness-options will fail."""

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "foo",
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
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_mismatched_hash():
    """
    Test that failure occurs when the actual file hash doesn't match the hash
    provided by harness-options.js.
    """

    harnessoptions = {
            "sdkVersion": "foo",
            "jetpackID": "foobar",
            "manifest":
                {"resource://bootstrap.js":
                    {"requirements": {},
                     "packageName": "addon-kit",
                     "moduleName": "drawing",
                     "jsSHA256": "",
                     "docsSHA256": ""}}}

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()

    err = _do_test(MockXPI({"bootstrap.js": bootstrap,
                            "resources/bootstrap.js": bootstrap,
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert err.failed()


def test_mismatched_db_hash():
    """
    Test that failure occurs when the hash of a file doesn't exist in the
    Jetpack known file database.
    """

    with open("jetpack/addon-sdk/python-lib/cuddlefish/"
                  "app-extension/bootstrap.js") as bootstrap_file:
        bootstrap = bootstrap_file.read()
        # Break the hash with this.
        bootstrap = "function() {}; %s" % bootstrap
        bootstrap_hash = hashlib.sha256(bootstrap).hexdigest()

    harnessoptions = {
            "sdkVersion": "foo",
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
                            "harness-options.json":
                                json.dumps(harnessoptions)}))
    print err.print_summary(verbose=True)
    assert not err.failed()

    assert "jetpack_loaded_modules" in err.metadata
    assert not err.metadata["jetpack_loaded_modules"]
    assert "jetpack_identified_files" in err.metadata

    assert "jetpack_unknown_files" in err.metadata
    nose.tools.eq_(err.metadata["jetpack_unknown_files"],
                   ["bootstrap.js",
                    "resources/bootstrap.js"])


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

