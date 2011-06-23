import validator.testcases.l10ncompleteness as l10n
from validator.testcases.l10n.dtd import DTDParser
from validator.testcases.l10n.properties import PropertiesParser
from validator.xpi import XPIManager
from validator.errorbundler import ErrorBundle
from validator.constants import *
from helper import MockXPI


def test_chromemanifest():
    "Make sure it only accepts packs with chrome.manifest files."

    assert l10n.test_lp_xpi(None, MockXPI()) is None


def test_parse_l10n():
    "Tests that the doc parser function returns the right values."

    assert isinstance(l10n._parse_l10n_doc("foo.dtd",
                                           "<!ENTITY foo 'bar'>"),
                      DTDParser)
    assert isinstance(l10n._parse_l10n_doc("foo.properties",
                                           "foo=bar"),
                      PropertiesParser)
    assert l10n._parse_l10n_doc("foo.bar",
                                "") is None


def test_results_aggregator():
    "Tests that language pack aggregation results are read properly."

    err = ErrorBundle()
    l10n._aggregate_results(err,
                            [{"type":"missing_files",
                              "filename":"foo.bar"}],
                            {"name": "en-US",
                             "target": "foo.bar",
                             "jarred": False})
    assert err.failed()

    err = ErrorBundle()
    l10n._aggregate_results(err,
                            [{"type":"missing_entities",
                              "filename":"foo.bar",
                              "missing_entities":["asdf","ghjk"]}],
                            {"name": "en-US",
                             "target": "foo.bar",
                             "jarred": False})
    assert err.failed()

    err = ErrorBundle()
    l10n._aggregate_results(err,
                            [{"type":"unchanged_entity",
                              "entities":0,
                              "unchanged_entities":[("asdf", 1), ("ghjk", 1)],
                              "filename":"foo.bar"},
                              {"type":"total_entities",
                               "entities":100}],
                            {"name": "en-US",
                             "target": "foo.bar",
                             "jarred": False})
    assert not err.failed()

    err = ErrorBundle()
    l10n._aggregate_results(err,
                            [{"type":"unchanged_entity",
                              "entities":50,
                              "unchanged_entities":[("asdf", 1), ("ghjk", 1)],
                              "filename":"foo.bar"},
                             {"type":"file_entity_count",
                              "filename":"foo.bar",
                              "entities":100},
                             {"type":"total_entities",
                              "entities":100}],
                            {"name": "en-US",
                             "target": "foo.bar",
                             "path": "/locale/en-US/",
                             "jarred": True})
    assert err.failed()
    print err.warnings
    assert all("//" not in "".join(m["file"]) for m in err.warnings)


def test_comparer():
    "Tests the function that compares two packages."

    ref = XPIManager("tests/resources/l10n/langpack/reference.jar")
    ref.locale_name = "en-US"
    extra_ref = XPIManager(
        "tests/resources/l10n/langpack/extra_files_ref.jar")
    pass_ = XPIManager("tests/resources/l10n/langpack/pass.jar")
    pass_.locale_name = "en-US"
    mfile = XPIManager(
        "tests/resources/l10n/langpack/missing_file.jar")
    mfile.locale_name = "en-US"
    extra = XPIManager(
        "tests/resources/l10n/langpack/extra_files.jar")
    extra.locale_name = "en-US"
    mfileent = XPIManager(
        "tests/resources/l10n/langpack/missing_file_entities.jar")
    mfileent.locale_name = "en-US"
    ment = XPIManager(
        "tests/resources/l10n/langpack/missing_entities.jar")
    ment.locale_name = "en-US"

    assert _compare_packs(ref, pass_) == 3
    assert _compare_packs(extra_ref, pass_) == 3
    assert _compare_packs(ref, extra) == 3
    assert _compare_packs(ref, mfile) == 4
    assert _compare_packs(ref, mfileent) == 3
    assert _compare_packs(ref, ref) > 3


def _compare_packs(reference, target):
    "Does a simple comparison and prints the output"

    comparison = l10n._compare_packages(reference, target)

    count = 0
    for error in comparison:
        if error["type"] != "unexpected_encoding":
            count += 1

    print comparison
    return count

