import fnmatch

from validator import decorator
from validator.constants import *


@decorator.register_test(1)
def test_conduittoolbar(err, xpi_manager=None):
    "Find and blacklist Conduit toolbars"

    # Ignore non-extension types
    if err.detected_type in (PACKAGE_ANY,
                             PACKAGE_THEME,
                             PACKAGE_SEARCHPROV):
        return None

    # Tests regarding the install.rdf file.
    if err.get_resource("has_install_rdf"):

        #Go out and fetch the install.rdf instance object
        install = err.get_resource("install_rdf")

        # Define a list of specifications to search for Conduit with
        parameters = {
            "http://www.conduit.com/": install.uri("homepageURL"),
            "Conduit Ltd.": install.uri("creator"),
            "More than just a toolbar.": install.uri("description")}

        # Iterate each specification and test for it.
        for k, uri_reference in parameters.items():
            # Retrieve the value
            results = install.get_object(None, uri_reference)
            # If the value exists, test for the appropriate content
            if results == k:
                err_mesg = "Conduit value (%s) found in install.rdf" % k
                return err.warning(("testcases_conduit",
                                    "test_conduittoolbar",
                                    "detected_rdf"),
                                   "Detected Conduit toolbar.",
                                   err_mesg,
                                   "install.rdf")

        # Also test for the update URL
        update_url_value = "https://ffupdate.conduit-services.com/"

        results = install.get_object(None, install.uri("updateURL"))
        if results and results.startswith(update_url_value):
            return err.warning(("testcases_conduit",
                                "test_conduittoolbar",
                                "detected_updateurl"),
                               "Detected Conduit toolbar.",
                               "Conduit update URL found in install.rdf.",
                               "install.rdf")

    # Do some matching on the files in the package
    conduit_files = ("components/Conduit*",
                     "searchplugin/conduit*")
    for file_ in xpi_manager:
        for bad_file in conduit_files:
            # If there's a matching file, it's Conduit
            if fnmatch.fnmatch(file_, bad_file):
                return err.warning(("testcases_conduit",
                                    "test_conduittoolbar",
                                    "detected_files"),
                                   "Detected Conduit toolbar.",
                                   "Conduit directory (%s) found." % bad_file)

    # Do some tests on the chrome.manifest file if it exists
    if "chrome.manifest" in xpi_manager:
        # Grab the chrome manifest
        chrome = err.get_resource("chrome.manifest")

        # Get all styles for customizing the toolbar
        data = chrome.get_value("style",
                    "chrome://global/content/customizeToolbar.xul")

        # If the style exists and it contains "ebtoolbarstyle"...
        if data is not None and \
           data["object"].count("ebtoolbarstyle") > 0:
            return err.warning(("testcases_conduit",
                                "test_conduittoolbar",
                                "detected_chrome_manifest"),
                               "Detected Conduit toolbar.",
                               "'ebtoolbarstyle' found in chrome.manifest",
                               filename=data["filename"],
                               line=data["line"],
                               context=chrome.context)

