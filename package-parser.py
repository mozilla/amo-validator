import sys

from xpi import XPIManager

def test_package(package):
    "Begins tests for the package."
    
    errors = []
    warnings = []
    
    # ---- Tier 1 Errors ----
    
    # Test that the package is an XPI.
    package_extension = package.split(".").pop()
    if package_extension.lower() != "xpi":
    
    # Load up a new instance of an XPI.
    p = XPIManager(package)
    if p == None:
        errors.append("The XPI could not be opened.")
        
    print p.get_file_data();
    
    # ---- End Tier 1 ----
    
    # Do we have any T1 errors?
    if len(errors) > 0:
        return compile_errors(1, errors, warnings)
    
    
    

def compile_errors(at_tier=1, errors=None, warnings=None):
    "Compiles warnings and errors into a neat little object."
    
    output = {"failed": true, # Fail by default
              "errors": errors,
              "warnings": warnings,
              "highest_tier": at_tier}
    
    if len(errors) == 0 and len(warnings) == 0:
        output["failed"] = false
    
    return output
    

# Start up the testing and return the output.
test_package(sys.argv[1])
