import fnmatch

import rdflib
from rdflib import URIRef

import rdf
import decorator
import chromemanifest
from chromemanifest import ChromeManifest

@decorator.register_test(1)
def test_conduittoolbar(eb, package_contents={}, xpi_manager=None):
    "Find and blacklist Conduit toolbars"
    
    # Ignore non-extension types
    if eb.detected_type in (0, 2, 5):
        return
    
    if eb.get_resource("has_install_rdf"):
        
        rdf = eb.get_resource("install_rdf")
        rdfDoc = rdf.rdf
        
        # Define a list of specifications to search for Conduit with
        parameters = {
            "http://www.conduit.com/": 
            URIRef("http://www.mozilla.org/2004/em-rdf#homepageURL"),
            "Conduit Ltd.":
            URIRef("http://www.mozilla.org/2004/em-rdf#creator"),
            "More than just a toolbar.":
            URIRef("http://www.mozilla.org/2004/em-rdf#description")}
        
        # We only have one outlier.
        updateURL = \
            URIRef("http://www.mozilla.org/2004/em-rdf#updateURL")
        
        # Iterate each specification and test for it.
        for k, v in parameters.items():
            # Retrieve the value
            results = list(rdfDoc.objects(None, v))
            # If the value exists, test for the appropriate content
            if results and results[0] == k:
                eb.reject = True
                return eb.error("Detected Conduit toolbar.")
        
        updateURL_value = "https://ffupdate.conduit-services.com/"
        
        results = list(rdfDoc.objects(None, updateURL))
        if results and results[0].startswith(updateURL_value):
            eb.reject = True
            return eb.error("Detected Conduit toolbar.")
        
        # Find some files
        conduit_files = ("components/Conduit*",
                         "searchplugin/conduit*")
        for f in package_contents:
            for cf in conduit_files:
                
                if fnmatch.fnmatch(f, cf):
                    eb.reject = True
                    return eb.error("Detected Conduit toolbar.")
        
    if "chrome.manifest" in package_contents:
        # Grab the chrome manifest
        if eb.get_resource("chrome.manifest"):
            # It's cached in the error bundler
            chrome = get_resource("chrome.manifest")
        else:
            # Not cached, so we grab it.
            chrome_data = xpi_manager.zf.read("chrome.manifest")
            chrome = ChromeManifest(chrome_data)
            eb.save_resource("chrome.manifest", chrome)
        
        # Get all styles for customizing the toolbar
        data = chrome.get_value("style",
                    "chrome://global/content/customizeToolbar.xul")
        
        if data is not None and \
           data["object"].count("ebtoolbarstyle") > 0:
            eb.reject = True
            return eb.error("Detected Conduit toolbar.")
        
        