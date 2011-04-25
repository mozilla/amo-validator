import os
import re

import validator.typedetection as typedetection
from validator.typedetection import detect_opensearch
from validator.chromemanifest import ChromeManifest
from validator.rdf import RDFParser
from validator.xpi import XPIManager
from validator import decorator

from constants import *

types = {0: "Unknown",
         1: "Extension/Multi-Extension",
         2: "Theme",
         3: "Dictionary",
         4: "Language Pack",
         5: "Search Provider"}

assumed_extensions = {"jar": PACKAGE_THEME,
                      "xml": PACKAGE_SEARCHPROV}


def prepare_package(err, path, expectation=0):
    "Prepares a file-based package for validation."

    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if err and not os.path.isfile(path):
        err.error(("main",
                   "prepare_package",
                   "not_found"),
                  "The package could not be found")
        return

    # Pop the package extension.
    package_extension = os.path.splitext(path)[1]
    package_extension = package_extension.lower()

    if package_extension == ".xml":
        return test_search(err, path, expectation)

    # Test that the package is an XPI.
    if package_extension not in (".xpi", ".jar"):
        if err:
            err.error(("main",
                       "prepare_package",
                       "unrecognized"),
                      "The package is not of a recognized type.")
        return False

    package = open(path, "rb")
    output = test_package(err, package, path, expectation)
    package.close()

    return output


def test_search(err, package, expectation=0):
    "Tests the package to see if it is a search provider."

    expected_search_provider = expectation in (PACKAGE_ANY,
                                               PACKAGE_SEARCHPROV)

    # If we're not expecting a search provider, warn the user and stop
    # testing it like a search provider.
    if not expected_search_provider:
        return err.warning(("main",
                            "test_search",
                            "extension"),
                           "Unexpected file extension.")

    # Is this a search provider?
    opensearch_results = detect_opensearch(package,
                                           listed=err.get_resource("listed"))

    if opensearch_results["failure"]:
        # Failed OpenSearch validation
        error_mesg = "OpenSearch: %s" % opensearch_results["error"]
        err.error(("main",
                   "test_search",
                   "general_failure"),
                  error_mesg)

        # We want this to flow back into the rest of the program if
        # the error indicates that we're not sure whether it's an
        # OpenSearch document or not.

        if "decided" not in opensearch_results or \
           opensearch_results["decided"]:
            return

    elif expected_search_provider:
        err.set_type(PACKAGE_SEARCHPROV)
        err.notice(("main",
                    "test_search",
                    "confirmed"),
                   "OpenSearch provider confirmed.")

    return


def test_package(err, file_, name, expectation=PACKAGE_ANY):
    "Begins tests for the package."

    # Load up a new instance of an XPI.
    package = XPIManager(file_, name)
    if not package.zf:
        # Die on this one because the file won't open.
        return err.error(("main",
                          "test_package",
                          "unopenable"),
                         "The XPI could not be opened.")

    # Test the XPI file for corruption.
    if package.test():
        return err.error(("main",
                          "test_package",
                          "corrupt"),
                         "XPI package appears to be corrupt.")

    if package.extension in assumed_extensions:
        assumed_type = assumed_extensions[package.extension]
        # Is the user expecting a different package type?
        if not expectation in (PACKAGE_ANY, assumed_type):
            err.error(("main",
                       "test_package",
                       "unexpected_type"),
                      "Unexpected package type (found theme)")

    # Cache a copy of the package contents.
    package_contents = package.get_file_data()

    # Test the install.rdf file to see if we can get the type that way.
    has_install_rdf = "install.rdf" in package_contents
    if has_install_rdf:
        _load_install_rdf(err, package, expectation)

    return test_inner_package(err, package_contents, package)


def _load_install_rdf(err, package, expectation):
    # Load up the install.rdf file.
    install_rdf_data = package.read("install.rdf")

    if re.search('<!doctype', install_rdf_data, re.I):
        err.save_resource("bad_install_rdf", True)
        return err.error(("main",
                          "test_package",
                          "doctype_in_installrdf"),
                         "DOCTYPEs are not permitted in install.rdf",
                         "The add-on's install.rdf file contains a DOCTYPE. "
                         "It must be removed before your add-on can be "
                         "validated.",
                         filename="install.rdf")

    install_rdf = RDFParser(install_rdf_data)

    if install_rdf.rdf is None or not install_rdf:
        return err.error(("main",
                          "test_package",
                          "cannot_parse_installrdf"),
                         "Cannot Parse install.rdf",
                         "The install.rdf file could not be parsed.",
                         filename="install.rdf")
    else:
        err.save_resource("has_install_rdf", True, pushable=True)
        err.save_resource("install_rdf", install_rdf, pushable=True)

    # Load up the results of the type detection
    results = typedetection.detect_type(err,
                                        install_rdf,
                                        package)

    if results is None:
        return err.error(("main",
                          "test_package",
                          "undeterminable_type"),
                         "Unable to determine add-on type",
                         "The type detection algorithm could not determine "
                         "the type of the add-on.")
    else:
        err.set_type(results)

    # Compare the results of the low-level type detection to
    # that of the expectation and the assumption.
    if not expectation in (PACKAGE_ANY, results):
        err.warning(("main",
                     "test_package",
                     "extension_type_mismatch"),
                    "Extension Type Mismatch",
                    'Type "%s" expected, found "%s")' % (
                                                    types[expectation],
                                                    types[results]))


def populate_chrome_manifest(err, package_contents, xpi_package):
    "Loads the chrome.manifest if it's present"

    if "chrome.manifest" in package_contents:
        chrome_data = xpi_package.read("chrome.manifest")
        chrome = ChromeManifest(chrome_data)
        err.save_resource("chrome.manifest", chrome, pushable=True)


def test_inner_package(err, package_contents, xpi_package):
    "Tests a package's inner content."

    populate_chrome_manifest(err, package_contents, xpi_package)

    # Iterate through each tier.
    for tier in sorted(decorator.get_tiers()):

        # Let the error bundler know what tier we're on.
        err.set_tier(tier)

        # Iterate through each test of our detected type.
        supported_versions = None
        for test in decorator.get_tests(tier, err.detected_type):
            # Test whether the test is app/version specific.
            if test["versions"] is not None:
                # Grab the detected versions
                if not supported_versions:
                    supported_versions = err.get_resource("supported_versions")
                # If there are no supported versions, the test is not
                # applicable or is unsupported.
                if not supported_versions:
                    continue

                found_version = False
                for guid in test["versions"].keys():
                    if (guid in supported_versions and
                        any((detected_version in test["versions"][guid]) for
                            detected_version in
                            supported_versions[guid])):
                        found_version = True
                        break
                # If none of the versions that the test supports are found,
                # skip the test.
                if not found_version:
                    continue

            test_func = test["test"]
            if test["simple"]:
                test_func(err)
            else:
                # Pass in:
                # - Error Bundler
                # - Package listing
                # - A copy of the package itself
                test_func(err, package_contents, xpi_package)

        # Return any errors at the end of the tier if undetermined.
        if err.failed(fail_on_warnings=False) and not err.determined:
            err.unfinished = True
            return err

    # Return the results.
    return err
