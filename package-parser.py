import sys
import os

import zipfile

import decorator
import rdf
import tests.typedetection
import tests.packagelayout
from xpi import XPIManager
from rdf import RDFTester
from errorbundler import ErrorBundle


def main(argv=None):
    "Main function. Handles delegation to other functions"
    if argv is None:
        argv = sys.argv
    
    expectations = {"any":0,
                    "extensions":1,
                    "themes":2,
                    "dictionaries":3,
                    "languagepacks":4,
                    "search":5,
                    "multi":1} # A multi extension is an extension
    
    # If we have a specified expectation, adhere to it.
    if len(argv) > 2:
        expectation = argv[2] # Grab from the command line
        if expectation in expectations:
            # Pair up the expectation with its associated type
            expectation = expectations[expectation]
        else:
            # Inform the user that their command is broke and move on
            print "We could not find the expected addon type."
            expectation = 0
            
    else:
        expectation = 0 # Default to any extension type
    
    error_bundle = ErrorBundle()
    
    results = test_package(error_bundle, argv[1], expectation)
    
    results.print_summary()
    

def test_package(eb, package, expectation=0):
    "Begins tests for the package."
    
    
    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if not os.path.exists(package):
        return eb.error("The package could not be found")
    
    print "Beginning test suite..."
    
    package_extension = os.path.splitext(package)[1]
    package_extension = package_extension.lower()
    
    # Test for OpenSearch providers
    if package_extension == ".xml":
        
        print "Detected possible OpenSearch provider..."
        
        expected_search_provider = expectation in (0, 5)
        
        # If we're not expecting a search provider, warn the user
        if not expected_search_provider:
            return eb.warning("Unexpected file extension.")
        
        # Is this a search provider?
        opensearch_results = \
            tests.typedetection.detect_opensearch(package)
        
        if opensearch_results["failure"]:
            # Failed OpenSearch validation
            error_mesg = "OpenSearch: %s" % opensearch_results["error"]
            eb.error(error_mesg)
            
            # We want this to flow back into the rest of the program. It
            # will validate against other things and make Tier 1 worth
            # it's weight in Python.
            
        elif expected_search_provider:
            eb.set_type(5)
            print "OpenSearch provider confirmed."
            return eb
            
    
    # Test that the package is an XPI.
    if not package_extension in (".xpi", ".jar"):
        eb.error("The package is not of a recognized type.")
    
    
    # Load up a new instance of an XPI.
    try:
        p = XPIManager(package)
        if p is None:
            # Die on this one because the file won't open.
            return eb.error("The XPI could not be opened.")
        
    except zipfile.BadZipfile:
        # This likely means that there is a problem with the zip file.
        return eb.error("The XPI file that was submitted is corrupt.")
    
    except IOError:
        # This means that there was something wrong with the command.
        return eb.error("We were unable to open the file for testing.")
    
    
    # Cache a copy of the package contents
    package_contents = p.get_file_data()
    
    assumed_extensions = {"jar": 2,
                          "xml": 5}
    
    if p.extension in assumed_extensions:
        assumed_type = assumed_extensions[p.extension]
        # Is the user expecting a different package type?
        if not expectation in (0, assumed_type):
            eb.error("Unexpected package type (found theme)")
    
    # Test the install.rdf file to see if we can get the type that way.
    if "install.rdf" in package_contents:
        # Load up the install.rdf file
        install_rdf_data = p.zf.read("install.rdf")
        install_rdf = RDFTester(install_rdf_data)
        
        # Load up the results of the type detection
        results = tests.typedetection.detect_type(install_rdf, p)
        eb.set_type(results)
        
        if results is None:
            return eb.error("Unable to determine addon type")
        
        # Compare the results of the low-level type detection to
        # that of the expectation and the assumption.
        if not expectation in (0, results):
            err_mesg = "File extension (%s) mismatch"
            err_mesg = err_mesg % p.extension
            eb.warning(err_mesg)
        
        
    
    # ---- Begin Tiers ----
    
    # Iterate through each tier
    for tier in decorator.get_tiers():
        
        print "Entering tier #%d" % tier
        
        # Iterate through each test
        for test in decorator.run_tests(tier):
            # Pass in:
            # - Error Bundler
            # - Package listing
            # - A copy of the package itself
            test(eb, package_contents, p)
        
        # Return any errors at the end of the tier
        if eb.failed():
            return eb
    
    
    # Return the results.
    return eb
    

# Start up the testing and return the output.
if __name__ == '__main__':
    main()


