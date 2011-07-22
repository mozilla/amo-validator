from StringIO import StringIO
from validator.errorbundler import ErrorBundle
from validator.testcases.l10ncompleteness import _get_locale_manager, \
                                                 _list_locales, \
                                                 _get_locales
import validator.testcases.l10ncompleteness as l10ncomp
from helper import MockXPI


def test_list_locales():
    "Tests that the appropriate locales are listed for a package"

    err = ErrorBundle()
    assert _list_locales(err) is None

    err.save_resource("chrome.manifest",
                      MockManifest([("locale", "foo", "bar"),
                                    ("locale", "abc", "def")]))
    assert len(_list_locales(err)) == 2

    err = ErrorBundle()
    result = _list_locales(err, MockXPI(
        {"chrome.manifest": "tests/resources/chromemanifest/chrome.manifest"}))
    assert result


def test_get_locales():
    "Tests that the proper locale descriptions are returned for a package"

    assert not (_get_locales(None,
                             None,
                             [{"object": "foo bar jar:nobang"}]))

    assert (_get_locales(None,
                         None,
                         [{"subject": "locale",
                           "predicate": "pred1",
                           "object": "loc1 /foo/bar"}]) ==
            {"pred1:loc1": {"predicate": "pred1",
                            "target": "/foo/bar",
                            "name": "loc1",
                            "jarred": False}})

    assert (_get_locales(None,
                         None,
                         [{"subject": "locale",
                           "predicate": "pred2",
                           "object": "loc2 jar:foo.jar!/bar/zap"}]) ==
            {"pred2:loc2": {"predicate": "pred2",
                            "target": "/bar/zap",
                            "path": "foo.jar",
                            "name": "loc2",
                            "jarred": True}})


def test_get_manager():
    "Tests that the proper XPI manager is returned for a locale description"

    # Test that jarred packages are simply returned
    assert _get_locale_manager(None, "foo", {"jarred": False}) == "foo"

    # Test that cached unjarred packages are fetched from the cache
    l10ncomp.LOCALE_CACHE = {"foo": "bar"}
    assert _get_locale_manager(None, None, {"jarred": True,
                                            "path": "foo"}) == "bar"

    # Test that when a broken path is referenced, a warning is thrown
    l10ncomp.LOCALE_CACHE = {}
    err = ErrorBundle()
    assert _get_locale_manager(err, MockXPI(), {"jarred": True,
                                                "path": "foo"}) is None
    assert err.failed()
    assert not l10ncomp.LOCALE_CACHE

    # Save the XPIManager that the L10n module is using and replace it
    xm = l10ncomp.XPIManager
    l10ncomp.XPIManager = MockManager

    # Test that the appropriate XPI is returned for a given input
    l10ncomp.LOCALE_CACHE = {}
    err = ErrorBundle()
    xpi = MockManager("testcase1")
    print xpi.read("bar.jar")
    result = _get_locale_manager(err,
                                 xpi,
                                 {"jarred": True,
                                  "path": "bar.jar"})
    assert isinstance(result, MockManager)
    print result.value
    assert result.value == "bar.jar:testcase1"
    assert result.path == "bar.jar"
    assert l10ncomp.LOCALE_CACHE["bar.jar"] == result

    # Test that no_cache works
    l10ncomp.LOCALE_CACHE = {}
    err = ErrorBundle()
    xpi = MockManager("testcase2")
    result = _get_locale_manager(err,
                                 xpi,
                                 {"jarred": True,
                                  "path": "foo.jar"},
                                 no_cache=True)
    assert not l10ncomp.LOCALE_CACHE

    # Restore everything to normal
    l10ncomp.LOCALE_CACHE = {}
    l10ncomp.XPIManager = xm


class MockManager(object):
    "Represents a fake XPIManager"

    def __init__(self, default, mode="r", name=None):
        if isinstance(default, StringIO):
            default = default.getvalue()
        elif isinstance(default, file):
            default = default.read()

        self.value = default
        self.path = name

    def __contains__(self, name):
        return True

    def read(self, filename):
        return "%s:%s" % (filename, self.value)


class MockManifest(object):
    "Represents a phony chrome.manifest"

    def __init__(self, locales):
        self.locales = locales

    def get_triples(self, subject):
        return self.locales

