import logging
import os
import re
import signal

from validator.typedetection import detect_type
from validator.opensearch import detect_opensearch
from validator.webapp import detect_webapp
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

log = logging.getLogger()


class ValidationTimeout(Exception):

    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return "Validation timeout after %d seconds" % self.timeout


def prepare_package(err, path, expectation=0, for_appversions=None,
                    timeout=None):
    """Prepares a file-based package for validation.

    timeout is the number of seconds before validation is aborted.
    If timeout is -1 then no timeout checking code will run.
    """
    if not timeout:
        timeout = 60  # seconds

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
    elif package_extension in (".json", ".webapp", ):
        return test_webapp(err, path, expectation)

    # Test that the package is an XPI.
    if package_extension not in (".xpi", ".jar"):
        if err:
            err.error(("main",
                       "prepare_package",
                       "unrecognized"),
                      "The package is not of a recognized type.")
        return False

    package = open(path, "rb")
    validation_state = {'complete': False}

    def timeout_handler(signum, frame):
        if validation_state['complete']:
            # There is no need for a timeout. This might be the result of
            # sequential validators, like in the test suite.
            return
        ex = ValidationTimeout(timeout)
        log.error("%s; Package: %s" % (str(ex), path))
        raise ex

    if timeout != -1:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)
    output = test_package(err, package, path, expectation,
                          for_appversions)
    package.close()
    validation_state['complete'] = True

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
    detect_opensearch(err, package, listed=err.get_resource("listed"))

    if expected_search_provider and not err.failed():
        err.set_type(PACKAGE_SEARCHPROV)
        err.notice(("main",
                    "test_search",
                    "confirmed"),
                   "OpenSearch provider confirmed.")


def test_webapp(err, package, expectation=0):
    "Tests the package to see if it is a search provider."

    expected_webapp = expectation in (PACKAGE_ANY, PACKAGE_WEBAPP)
    if not expected_webapp:
        return err.warning(
            err_id=("main", "test_webapp", "extension"),
            warning="Unexpected file extension.",
            description="An unexpected file extension was encountered.")

    detect_webapp(err, package)

    if expected_webapp and not err.failed():
        err.set_type(PACKAGE_WEBAPP)
        err.notice(("main",
                    "test_webapp",
                    "confirmed"),
                   "App confirmed.")


def test_package(err, file_, name, expectation=PACKAGE_ANY,
                 for_appversions=None):
    "Begins tests for the package."

    # Load up a new instance of an XPI.
    try:
        package = XPIManager(file_, mode="r", name=name)
    except:
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

    # Test the install.rdf file to see if we can get the type that way.
    has_install_rdf = "install.rdf" in package
    if has_install_rdf:
        _load_install_rdf(err, package, expectation)

    try:
        output = test_inner_package(err, package, for_appversions)
    except ValidationTimeout as ex:
        err.error(
                err_id=("main", "test_package", "timeout"),
                error="Validation timed out",
                description=["The validation process took too long to "
                             "complete. Contact an addons.mozilla.org editor "
                             "for more information.",
                             str(ex)])
        output = None

    return output


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
    results = detect_type(err, install_rdf, package)

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
                    ["We detected that the add-on's type does not match the "
                     "expected type.",
                     'Type "%s" expected, found "%s")' %
                         (types[expectation], types[results])])


def populate_chrome_manifest(err, xpi_package):
    "Loads the chrome.manifest if it's present"

    if "chrome.manifest" in xpi_package:
        chrome_data = xpi_package.read("chrome.manifest")
        chrome = ChromeManifest(chrome_data, "chrome.manifest")

        chrome_recursion_buster = set()

        # Handle the case of manifests linked from the manifest.
        def get_linked_manifest(path, from_path, from_chrome, from_triple):

            if path in chrome_recursion_buster:
                err.warning(
                    err_id=("submain", "populate_chrome_manifest",
                            "recursion"),
                    warning="Linked manifest recursion detected.",
                    description="A chrome registration file links back to "
                                "itself. This can cause a multitude of "
                                "issues.",
                    filename=path)
                return

            # Make sure the manifest is properly linked
            if path not in xpi_package:
                err.notice(
                    err_id=("submain", "populate_chrome_manifest", "linkerr"),
                    notice="Linked manifest could not be found.",
                    description=["A linked manifest file could not be found "
                                 "in the package.",
                                 "Path: %s" % path],
                    filename=from_path,
                    line=from_triple["line"],
                    context=from_chrome.context)
                return

            chrome_recursion_buster.add(path)

            manifest = ChromeManifest(xpi_package.read(path), path)
            for triple in manifest.triples:
                yield triple

                if triple["subject"] == "manifest":
                    for subtriple in get_linked_manifest(
                            triple["predicate"], path, manifest, triple):
                        yield subtriple

            chrome_recursion_buster.discard(path)

        chrome_recursion_buster.add("chrome.manifest")

        # Search for linked manifests in the base manifest.
        for extra_manifest in chrome.get_triples(subject="manifest"):
            # When one is found, add its triples to our own.
            for triple in get_linked_manifest(extra_manifest["predicate"],
                                              "chrome.manifest", chrome,
                                              extra_manifest):
                chrome.triples.append(triple)

        chrome_recursion_buster.discard("chrome.manifest")

        # Create a reference so we can get the chrome manifest later, but make
        # it pushable so we don't run chrome manifests in JAR files.
        err.save_resource("chrome.manifest", chrome, pushable=True)
        # Create a non-pushable reference for tests that need to access the
        # chrome manifest from within JAR files.
        err.save_resource("chrome.manifest_nopush", chrome, pushable=False)


def test_inner_package(err, xpi_package, for_appversions=None):
    "Tests a package's inner content."

    populate_chrome_manifest(err, xpi_package)

    # Iterate through each tier.
    for tier in sorted(decorator.get_tiers()):

        # Let the error bundler know what tier we're on.
        err.set_tier(tier)

        # Iterate through each test of our detected type.
        for test in decorator.get_tests(tier, err.detected_type):
            # Test whether the test is app/version specific.
            if test["versions"] is not None:
                # If the test's version requirements don't apply to the add-on,
                # then skip the test.
                if not err.supports_version(test["versions"]):
                    continue

                # If the user's version requirements don't apply to the test or
                # to the add-on, then skip the test.
                if (for_appversions and
                    not (err._compare_version(requirements=for_appversions,
                                              support=test["versions"]) and
                         err.supports_version(for_appversions))):
                    continue

            # Save the version requirements to the error bundler.
            err.version_requirements = test["versions"]

            test_func = test["test"]
            if test["simple"]:
                test_func(err)
            else:
                # Pass in:
                # - Error Bundler
                # - A copy of the package itself
                test_func(err, xpi_package)

        # Return any errors at the end of the tier if undetermined.
        if err.failed(fail_on_warnings=False) and not err.determined:
            err.unfinished = True
            err.discard_unused_messages(ending_tier=tier)
            return err

    # Return the results.
    return err
