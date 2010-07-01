import testcases.l10ncompleteness as l10n
from testcases.l10n.dtd import DTDParser
from testcases.l10n.properties import PropertiesParser
from xpi import XPIManager
from errorbundler import ErrorBundle
from helper import _do_test
from constants import *

def test_chromemanifest():
    "Make sure it only accepts packs with chrome.manifest files."
    
    assert l10n.test_lp_xpi(None, {}, None) is None
    

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
    
    err = ErrorBundle(None, True)
    l10n._aggregate_results(err,
                            [{"type":"missing_files",
                              "filename":"foo.bar"}],
                            {"name":"en-US"})
    assert err.failed()
    
    err = ErrorBundle(None, True)
    l10n._aggregate_results(err,
                            [{"type":"missing_entities",
                              "filename":"foo.bar",
                              "missing_entities":["asdf","ghjk"]}],
                            {"name":"en-US"})
    assert err.failed()
    
    err = ErrorBundle(None, True)
    l10n._aggregate_results(err,
                            [{"type":"unchanged_entities",
                              "entities":0,
                              "unchanged_entities":["asdf","ghjk"],
                              "filename":"foo.bar"},
                              {"type":"total_entities",
                               "entities":100}],
                            {"name":"en-US"})
    assert not err.failed()
    
    err = ErrorBundle(None, True)
    l10n._aggregate_results(err,
                            [{"type":"unchanged_entities",
                              "entities":50,
                              "unchanged_entities":["asdf","ghjk"],
                              "filename":"foo.bar"},
                              {"type":"total_entities",
                               "entities":100}],
                            {"name":"en-US"})
    assert err.failed()
    

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
    
    assert len(l10n._compare_packages(ref, pass_)) == 1
    assert len(l10n._compare_packages(extra_ref, pass_)) == 1
    assert len(l10n._compare_packages(ref, extra)) == 1
    assert len(l10n._compare_packages(ref, mfile)) == 2
    assert len(l10n._compare_packages(ref, mfileent)) == 2
    assert len(l10n._compare_packages(ref, ref)) > 1
    
