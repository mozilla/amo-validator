from nose.tools import eq_

from .js_helper import TestCase, _test_xpi
from .test_frameworks import disposable_metadata

from validator import constants
from validator.testcases import libraries
from validator.xpi import XPIManager


BASE_PATH = "tests/resources/libraryblacklist/"


def _do_test(name):
    return _test_xpi(BASE_PATH + name)


def test_whitelisted_files():
    """
    Tests the validator's ability to hash each individual file and (based on
    this information) determine whether the addon passes or fails the
    validation process.
    """

    err = _do_test("blocked.xpi")

    identified_files = err.metadata.get("identified_files")
    print err.metadata
    eq_(identified_files,
        {"test.js":
            {"sources": [["fake-library",
                          "null",
                          "This file is a false script to facilitate "
                          "testing of library blacklisting."]]}})

    assert not err.notices
    assert not err.failed()


def test_skip_whitelisted_file():
    """Ensure whitelisted files are skipped for processing."""

    err = _do_test("errors.xpi")

    identified_files = err.metadata.get("identified_files")
    eq_(identified_files,
        {"jquery.1.6.4.min.jquery-1.6.4.min.js":
            {"sources": [["jquery",
                          "1.6.4",
                          "minified/jquery-1.6.4.min.js"]]}})

    assert not err.notices
    assert not err.failed()


def test_validate_libs_in_compat_mode():
    err = _do_test("addon_with_mootools.xpi")

    assert err.get_resource("scripts"), \
        "expected mootools scripts to be marked for proessing"
    eq_(err.get_resource("scripts")[0]["scripts"],
        set(["content/mootools.js"]))


def test_library_messages():
    messages = ("I'm a leaf on the wind.",
                "Watch how I soar.")

    with disposable_metadata() as metadata:
        jquery = metadata["libraries"]["jquery"]
        jquery["messages"] = [messages[0]]
        jquery["versions"]["1.6.4"]["messages"] = [messages[1]]

        err = _do_test("errors.xpi")

        assert not err.errors
        assert err.notices
        notice = err.notices[0]

        eq_(notice["id"],
            ("testcases_libraries", "detect_libraries",
             "detected_library_message"))
        assert all(m in notice["description"]
                   for m in messages)


def test_banned_library():
    messages = ["I'm a leaf on the wind.",
                "Watch how I soar."]

    with disposable_metadata() as metadata:
        jquery = metadata["libraries"]["jquery"]
        jquery["messages"] = [messages[0]]
        jquery["versions"]["1.6.4"]["messages"] = [messages[1]]

        with open(BASE_PATH + "errors.xpi") as file:
            path = "jquery.1.6.4.min.jquery-1.6.4.min.js"
            hash = libraries.checksum(path, XPIManager(file).read(path))
        metadata["hashes"][hash]["deprecated"] = constants.DEPRECATED_HARD
        metadata["hashes"][hash]["messages"] = messages

        err = _do_test("errors.xpi")

        assert err.errors
        error = err.errors[0]

        eq_(error["id"],
            ("testcases_libraries", "detect_libraries",
             "deprecated_js_library"))
        assert all(msg in error["description"]
                   for msg in messages)


class TestDataValidation(TestCase):

    def _check(self, data):
        try:
            libraries.validate_metadata(data)
        except AssertionError:
            return False

        return True

    def _check_library(self, **kw):
        return self._check({'frameworks': {},
                            'libraries': {
                                'lib-id': kw},
                            'hashes': {}})

    def _check_version(self, **kw):
        version = {'files': {}}
        version.update(kw)
        return self._check_library(versions={'1.0': version})

    def _check_hash(self, **kw):
        hash = kw.pop('hash',
                      'a2c064616af4c66c576821616646bdfa'
                      'd5556a263b4b007847605118971f4389')

        hashes = {hash: {
            'sources': [
                ['library', 'version', 'path']]}}
        hashes[hash].update(kw)

        return self._check({
            'libraries': {},
            'frameworks': {},
            'hashes': hashes})

    def test_skeleton_library(self):
        """Tests that a skeleton library passes validation."""

        assert self._check_library()
        assert self._check_version()

    def test_fail_invalid_messages(self):
        """Tests that invalid messages data causes failure."""

        for thing in 'foo', {}, 42, True, None:
            assert not self._check_library(messages=thing)
            assert not self._check_version(messages=thing)
            assert not self._check_hash(messages=thing)

        for thing in {}, 42, True, None:
            assert not self._check_library(messages=[thing])
            assert not self._check_version(messages=[thing])
            assert not self._check_hash(messages=[thing])

        assert self._check_library(messages=['foo', 'bar'])
        assert self._check_version(messages=['foo', 'bar'])
        assert self._check_hash(messages=['foo', 'bar'])

    def test_missing_sections(self):
        """Tests that data with missing sections fails."""

        sections = 'frameworks', 'libraries', 'hashes'
        data = dict((sect, {}) for sect in sections)

        assert self._check(data)

        for sect in sections:
            d = data.copy()
            del d[sect]
            assert not self._check(d)

            for thing in [], 'foo', 42, True:
                d = data.copy()
                d[sect] = thing
                assert not self._check(d)

    def test_invalid_hashes(self):
        """Tests that invalid hashes are not accepted."""

        assert self._check_hash()

        assert not self._check_hash(hash='foo')

        for thing in {}, 'foo', 42, True:
            assert not self._check_hash(sources=thing)
            assert not self._check_hash(sources=[thing])

        for thing in {}, 42, True:
            assert not self._check_hash(sources=[[thing, thing, thing]])

    def test_stock_hashes(self):
        """Tests that the stock hashes are accepted."""

        assert self._check(constants.LIBRARY_METADATA)
