from contextlib import contextmanager
from copy import deepcopy
from itertools import chain
import json

from nose.tools import eq_

from .js_helper import _test_xpi

from validator import constants
from validator.testcases.frameworks import fake_version


KNOWN_SCRIPT = ("This file is a false script to facilitate testing of library "
                "blacklisting.")


class MockXPI(object):

    def __init__(self, resources):
        self.resources = resources

    def info(self, name):
        return {"extension": name.split(".")[-1].lower()}

    def read(self, name):
        if isinstance(self.resources[name], bool):
            # For legacy code, files specified as `True` return an
            # empty string as their contents.
            return ""
        if isinstance(self.resources[name], (dict, list, tuple)):
            return json.dumps(self.resources[name])
        return self.resources[name]

    def __iter__(self):
        for name in self.resources.keys():
            yield name

    def __contains__(self, name):
        return name in self.resources


@contextmanager
def accepted_version(*path):
    """
    Temporarily marks the library, framework, or version at the given path
    as accepted. Used mainly for tests on now-banned, outdated Jetpack
    versions.
    """
    dict_ = constants.LIBRARY_METADATA
    for elem in path:
        dict_ = dict_[elem]

    # If this doesn't exist, it needs to be removed entirely. Any
    # other value needs to be restored. `unset` acts as a sentinel
    # that we know can't have been stored by any other code.
    unset = object()
    prev = dict_.get("deprecated", unset)
    dict_["deprecated"] = 0

    yield

    if prev is unset:
        del dict_["deprecated"]
    else:
        dict_["deprecated"] = prev


@contextmanager
def disposable_metadata():
    """
    Temporarily replaces the library metadata object with a deep copy which
    can be modified at will by a test case.
    """
    # We need to actually backup and restore the contents of the
    # metadata object, in case code imports the symbol itself rather
    # than the `constants` package.
    orig = constants.LIBRARY_METADATA.items()
    constants.LIBRARY_METADATA.clear()
    constants.LIBRARY_METADATA.update(deepcopy(orig))

    yield constants.LIBRARY_METADATA

    constants.LIBRARY_METADATA.clear()
    constants.LIBRARY_METADATA.update(orig)


def assert_framework_files(err, files):
    """Tests that all files are marked as pretested."""

    identified_files = err.metadata.get("identified_files")
    framework_files = err.metadata.get("framework_files")
    assert identified_files and framework_files

    for file in files:
        assert file in identified_files
        assert file in framework_files


def test_skeleton_framework_identification():
    """
    Tests that skeleton add-ons are detected as belonging to the correct
    framework, and rejected if applicable.
    """

    VERSION = "42"
    FRAMEWORKS = {
        "besttoolbars": {
            "unversioned": True,
            "framework_files": {
                "chrome/content/framework.js": "//Foo besttoolbars bar",
                "chrome/content/config.json": {}}},
        "conduit": {
            "deprecated": constants.DEPRECATED_HARD,
            "framework_files": {
                "searchplugins/conduit.xml": KNOWN_SCRIPT,
                "components/ConduitFoo.js": True}},
        "crossrider": {
            "deprecated": constants.DEPRECATED_HARD,
            "framework_files": {
                "chrome/content/CrossriderEXT.js": True,
                "chrome/content/crossrider.js": True,
                "chrome/content/crossriderapi.js": True}},
        # Don't bother with Jetpack here. It has a whole file
        # dedicated to it.
        "kango": {
            "framework_files": {"bootstrap.js": True,
                                "extension_info.json": {
                                    "kango_version": VERSION},
                                "kango/foo.js": True,
                                "kango-ui/bar.js": True}},
        "openforge": {
            "deprecated": constants.DEPRECATED_HARD,
            "framework_files": {
                "resources/f/data/forge/all.js": True},
            # Need to include some Jetpack-ish files to make sure
            # this is identified as Forge even though it's built on
            # Jetpack.
            "other_files": {
                "bootstrap.js": True,
                "harness-options.json":
                    {"sdkVersion": "1.8"}}},
        "scriptify": {
            "framework_files": {"bootstrap.js": True,
                                "scriptify.json":
                                    {"scriptify-version": VERSION}}},
    }

    for framework_id, data in FRAMEWORKS.iteritems():
        xpi = MockXPI(dict(chain(data["framework_files"].iteritems(),
                                 data.get("other_files", {}).iteritems())))
        err = _test_xpi(xpi)

        framework = err.metadata["framework"]

        eq_(framework["id"], framework_id)

        if data.get("deprecated"):
            # We don't bother reporting framework files for # deprecated
            # frameworks, since they're blanket rejected and won't
            # see further review.
            assert (("testcases_frameworks", "deprecated_framework") in
                    (e["id"] for e in err.errors))
        else:
            eq_(set(data["framework_files"]),
                set(err.metadata["framework_files"]))

            if data.get("unversioned"):
                files = [k for k in data["framework_files"]
                         if k.endswith(".js")]
                eq_(framework["version"],
                    fake_version(map(xpi.read, sorted(files))))
            else:
                eq_(framework["version"], VERSION)
