import sys
import os

import zipfile
from StringIO import StringIO

import argparse
import decorator
import typedetection
import testcases.packagelayout
import testcases.installrdf
import testcases.library_blacklist
import testcases.conduit
import testcases.langpack
import testcases.themes
import testcases.content
import testcases.targetapplication
import testcases.l10ncompleteness
from xpi import XPIManager
from rdf import RDFParser
from errorbundler import ErrorBundle
from constants import *

def main():
    "Main function. Handles delegation to other functions."

    expectations = {"any":0,
                    "extension":1,
                    "theme":2,
                    "dictionary":3,
                    "languagepack":4,
                    "search":5,
                    "multi":1} # A multi extension is an extension

    # Parse the arguments that
    parser = argparse.ArgumentParser(
        description="Run tests on a Mozilla-type addon.")

    parser.add_argument("package",
                        help="The path of the package you're testing")
    parser.add_argument("-t",
                        "--type",
                        default="any",
                        choices=expectations.keys(),
                        help="Type of addon you assume you're testing",
                        required=False)
    parser.add_argument("-o",
                        "--output",
                        default="text",
                        choices=("text", "json"),
                        help="The output format that you expect",
                        required=False)
    parser.add_argument("-v",
                        "--verbose",
                        action="store_const",
                        const=True,
                        help="""If the output format supports it, makes
                        the analysis summary include extra info.""")
    parser.add_argument("--file",
                        type=argparse.FileType("w"),
                        default=sys.stdout,
                        help="""Specifying a path will write the output
                        of the analysis to a file rather than to the
                        screen.""")
    parser.add_argument("--boring",
                        action="store_const",
                        const=True,
                        help="""Activating this flag will remove color
                        support from the terminal.""")
    parser.add_argument("--selfhosted",
                        action="store_const",
                        const=True,
                        help="""Indicates that the addon will not be
                        hosted on addons.mozilla.org. This allows the
                        <em:updateURL> element to be set.""")

    args = parser.parse_args()

    error_bundle = ErrorBundle(args.file,
        not args.file == sys.stdout or args.boring)

    # Emulates the "$status" variable in the original validation.php
    # test file. Equal to "$status == STATUS_LISTED".
    error_bundle.save_resource("listed", not args.selfhosted)

    # Parse out the expected add-on type and run the tests.
    expectation = expectations[args.type]
    prepare_package(error_bundle, args.package, expectation)

    # Print the output of the tests based on the requested format.
    if args.output == "text":
        error_bundle.print_summary(args.verbose)
    elif args.output == "json":
        error_bundle.print_json()

    # Close the output stream.
    args.file.close()

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)


def prepare_package(err, path, expectation=0):
    "Prepares a file-based package for validation."

    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if not os.path.isfile(path):
        err.reject = True
        return err.error("The package could not be found")

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
        err.error("The package is not of a recognized type.")

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
        return err.warning("Unexpected file extension.")

    # Is this a search provider?
    opensearch_results = \
        testcases.typedetection.detect_opensearch(package)

    if opensearch_results["failure"]:
        # Failed OpenSearch validation
        error_mesg = "OpenSearch: %s" % opensearch_results["error"]
        err.error(error_mesg)

        # We want this to flow back into the rest of the program if
        # the error indicates that we're not sure whether it's an
        # OpenSearch document or not.

        if not "decided" in opensearch_results or \
           opensearch_results["decided"]:
            err.reject = True
            return err

    elif expected_search_provider:
        err.set_type(PACKAGE_SEARCHPROV)
        err.info("OpenSearch provider confirmed.")

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
            return err.error("The XPI could not be opened.")

    except zipfile.BadZipfile:
        # This likely means that there is a problem with the zip file.
        return err.error("The XPI file that was submitted is corrupt.")

    except IOError:
        # This means that there was something wrong with the command.
        return err.error("We were unable to open the file for testing.")

    # Test the XPI file for corruption.
    if not package.test():
        err.reject = True
        return err.error("XPI package appears to be corrupt.")

    assumed_extensions = {"jar": PACKAGE_THEME,
                          "xml": PACKAGE_SEARCHPROV}

    if package.extension in assumed_extensions:
        assumed_type = assumed_extensions[package.extension]
        # Is the user expecting a different package type?
        if not expectation in (PACKAGE_ANY, assumed_type):
            err.error("Unexpected package type (found theme)")

    # Cache a copy of the package contents.
    package_contents = package.get_file_data()

    # Test the install.rdf file to see if we can get the type that way.
    has_install_rdf = "install.rdf" in package_contents
    err.save_resource("has_install_rdf", has_install_rdf)
    if has_install_rdf:
        # Load up the install.rdf file.
        install_rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(install_rdf_data)

        # Save a copy for later tests.
        err.save_resource("install_rdf", install_rdf)

        # Load up the results of the type detection
        results = typedetection.detect_type(err,
                                            install_rdf,
                                            package)

        if results is None:
            return err.error("Unable to determine addon type")
        else:
            err.set_type(results)

        # Compare the results of the low-level type detection to
        # that of the expectation and the assumption.
        if not expectation in (PACKAGE_ANY, results):
            err.reject = True
            err_mesg = "Extension type mismatch (expected %s, found %s)"
            err_mesg = err_mesg % (types[expectation], types[results])
            err.warning(err_mesg)

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

        # Return any errors at the end of the tier.
        if err.failed():
            return err


    # Return the results.
    return err

# Start up the testing and return the output.
if __name__ == '__main__':
    main()
