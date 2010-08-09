import os

import zipfile

import validator.testcases as testcases
import validator.typedetection as typedetection
from validator.typedetection import detect_opensearch
from validator.xpi import XPIManager
from validator.rdf import RDFParser
from validator import decorator
from validator.constants import *


def prepare_package(err, path, expectation=0):
    "Prepares a file-based package for validation."

    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if not os.path.isfile(path):
        err.reject = True
        return err.error(("main",
                          "prepare_package",
                          "not_found"),
                         "The package could not be found")

    # Pop the package extension.
    package_extension = os.path.splitext(path)[1]
    package_extension = package_extension.lower()

    if package_extension == ".xml":
        test_search(err, path, expectation)
        # If it didn't bork, it must be a valid provider!
        if not err.failed():
            return err

    # Test that the package is an XPI.
    if not package_extension in (".xpi", ".jar"):
        err.reject = True
        err.error(("main",
                   "prepare_package",
                   "unrecognized"),
                  "The package is not of a recognized type.")

    package = open(path)
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
        err.reject = True
        return err.warning(("main",
                            "test_search",
                            "extension"),
                           "Unexpected file extension.")
                           
    # Is this a search provider?
    opensearch_results = detect_opensearch(package)
    
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

        if not "decided" in opensearch_results or \
           opensearch_results["decided"]:
            err.reject = True
            return err

    elif expected_search_provider:
        err.set_type(PACKAGE_SEARCHPROV)
        err.info(("main",
                  "test_search",
                  "confirmed"),
                 "OpenSearch provider confirmed.")

    return err


def test_package(err, package, name, expectation=PACKAGE_ANY):
    "Begins tests for the package."

    types = {0: "Unknown",
             1: "Extension/Multi-Extension",
             2: "Theme",
             3: "Dictionary",
             4: "Language Pack",
             5: "Search Provider"}
             
    # Load up a new instance of an XPI.
    try:
        package = XPIManager(package, name)
        if package is None:
            # Die on this one because the file won't open.
            return err.error(("main",
                              "test_package",
                              "unopenable"),
                             "The XPI could not be opened.")
                             
    except zipfile.BadZipfile:
        # This likely means that there is a problem with the zip file.
        return err.error(("main",
                          "test_package",
                          "bad_zip"),
                         "The XPI file that was submitted is corrupt.")
                         
    except IOError:
        # This means that there was something wrong with the command.
        return err.error(("main",
                          "test_package",
                          "unable_to_open_package"),
                        "We were unable to open the file for testing.")
                        
    # Test the XPI file for corruption.
    if package.test():
        err.reject = True
        return err.error(("main",
                          "test_package",
                          "corrupt"),
                         "XPI package appears to be corrupt.")
                         
    assumed_extensions = {"jar": PACKAGE_THEME,
                          "xml": PACKAGE_SEARCHPROV}
                          
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
    err.save_resource("has_install_rdf", has_install_rdf)
    if has_install_rdf:
        # Load up the install.rdf file.
        install_rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(install_rdf_data)
        
        if install_rdf.rdf is None:
            return err.error(("main",
                              "test_package",
                              "cannot_parse_installrdf"),
                             "Cannot Parse install.rdf",
                             "The install.rdf file could not be parsed.")
        
        # Save a copy for later tests.
        err.save_resource("install_rdf", install_rdf)
        
        # Load up the results of the type detection
        results = typedetection.detect_type(err,
                                            install_rdf,
                                            package)
        
        if results is None:
            return err.error(("main",
                              "test_package",
                              "undeterminable_type"),
                             "Unable to determine addon type",
                             """The type detection algorithm could not
                             determine the type of the add-on.""")
        else:
            err.set_type(results)
        
        # Compare the results of the low-level type detection to
        # that of the expectation and the assumption.
        if not expectation in (PACKAGE_ANY, results):
            err.reject = True
            err.warning(("main",
                         "test_package",
                         "extension_type_mismatch"),
                        "Extension Type Mismatch",
                        'Type "%s" expected, found "%s")' % (
                                                        types[expectation],
                                                        types[results]))
    
    return test_inner_package(err, package_contents, package)

def test_inner_package(err, package_contents, package):
    "Tests a package's inner content."
    
    # Iterate through each tier.
    for tier in sorted(decorator.get_tiers()):
        # Iterate through each test of our detected type
        for test in decorator.get_tests(tier, err.detected_type):
            test_func = test["test"]
            if test["simple"]:
                test_func(err)
            else:
                # Pass in:
                # - Error Bundler
                # - Package listing
                # - A copy of the package itself
                test_func(err, package_contents, package)
        
        # Return any errors at the end of the tier if undetermined.
        if err.failed() and not err.determined:
            return err
            
    # Return the results.
    return err