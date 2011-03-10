from validator.errorbundler import ErrorBundle
from validator.testcases.l10ncompleteness import _get_locale_manager, \
                                                 _list_locales, \
                                                 _get_locales
import validator.testcases.l10ncompleteness as l10ncomp


def test_list_locales():
    "Tests that the appropriate locales are listed for a package"

    err = ErrorBundle()
    assert _list_locales(err) is None

    err.save_resource("chrome.manifest",
                      MockManifest([("locale", "foo", "bar"),
                                    ("locale", "abc", "def")]))
    assert len(_list_locales(err)) == 2


def test_get_locales():
    "Tests that the proper locale descriptions are returned for a package"

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

    assert _get_locale_manager(None, None, "foo", {"jarred": False}) == "foo"

    l10ncomp.LOCALE_CACHE = {"foo": "bar"}
    assert _get_locale_manager(None, None, None, {"jarred": True,
                                                  "path": "foo"}) == "bar"

    l10ncomp.LOCALE_CACHE = {}
    err = ErrorBundle()
    assert _get_locale_manager(err, {}, None, {"jarred": True,
                                               "path": "foo"}) is None
    assert err.failed()


class MockManager(object):
    "Represents a fake XPIManager"

    def read(self, filename):
        return None


class MockManifest(object):
    "Represents a phony chrome.manifest"

    def __init__(self, locales):
        self.locales = locales

    def get_triples(self, subject):
        return self.locales

