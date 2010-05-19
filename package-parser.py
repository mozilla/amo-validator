import sys
import getopt
import os

import zipfile

from xpi import XPIManager


def main(argv=None):
    "Main function. Handles delegation to other functions"
    if argv is None:
        argv = sys.argv
    
    results = test_package(argv[1])
    
    print "Summary:"
    if bool(results["failed"]):
        print "Test failed!\n"
        for error in results["errors"]:
            print "Error: %s" % error
        for warning in results["warnings"]:
            print "Warning: %s" % warning
    else:
        print "Test succeeded!"
    

def test_package(package):
    "Begins tests for the package."
    
    errors = []
    warnings = []
    
    
    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if not os.path.exists(package):
        errors.append("The package could not be found.")
        return compile_errors(0, errors, warnings)
    
    
    # ---- Tier 1 Errors ----
    
    # Test that the package is an XPI.
    package_extension = package.split(".").pop()
    if package_extension.lower() != "xpi":
        errors.append("The package is not of type 'XPI'")
    
    # Load up a new instance of an XPI.
    try:
        p = XPIManager(package)
        if p is None:
            errors.append("The XPI could not be opened.")
            # Die on this one because the file won't open.
            return compile_errors(1, errors, warnings)
        
    except zipfile.BadZipfile:
        # This likely means that there is a problem with the zip file.
        errors.append("The XPI file that was submitted is corrupt.")
        return compile_errors(1, errors, warnings)
    
    except IOError:
        # This means that there was something wrong with the command.
        errors.append("We were unable to open the file for testing.")
        return compile_errors(1, errors, warnings)
    
    
    # Next few tests will search for extension layout errors.
    package_contents = p.get_file_data()
    
    # Test for blacklisted file extensions
    blacklisted_extensions = ("dll", "exe", "dylib", "so",
                              "sh", "class", "swf")
    pattern = "File '%s' is using a blacklisted file extension (%s)"
    for name, file_ in package_contents.items():
        # Simple test to ensure that the extension isn't blacklisted
        if file_["extension"] in blacklisted_extensions:
            warnings.append(pattern % (name, file_extension))
    
    
    
    # ---- End Tier 1 ----
    
    
    # Do we have any T1 errors?
    if errors > 0 or warnings > 0:
        return compile_errors(1, errors, warnings)
    
    
    # ---- Tier 2 Errors ----
    
    
    # ---- End Tier 2 ----
    
    # Return the results.
    return compile_errors(2, errors, warnings)
    

def compile_errors(at_tier=1, errors=None, warnings=None):
    "Compiles warnings and errors into a neat little object."
    
    output = {"failed": bool(errors or warnings),
              "errors": errors,
              "warnings": warnings,
              "highest_tier": at_tier}
    
    return output
    

# Start up the testing and return the output.
if __name__ == '__main__':
    main()


