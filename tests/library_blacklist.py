import os

import hashlib

import decorator

@decorator.register_test(1)
def test_library_blacklist(eb, package_contents={}, xpi_package=None):
    """Test to make sure that the user isn't trying to sneak a JS
    library into their XPI. This tests for:
    - All jQuery
    - All Prototype
    - Most SWFObject
    - Some MooTools
    - Some dojo"""
    
    # Read in the definitions for the JS libraries we block
    definition_file = open("hashes.txt")
    definition_data = definition_file.read()
    
    definition_file.close()
    
    # Generate a tuple of definition data
    definitions = tuple(definition_data.split("\n"))
    
    # Iterate each file
    files = package_contents.keys()
    for f in files:
        # Open and hash the file
        s = hashlib.sha1()
        data = xpi_package.zf.read(f)
        s.update(data)
        
        # Hash the file
        h = s.hexdigest()
        
        # Test if the file is blocked
        if h in definitions:
            eb.error("File (%s) is a blacklisted JS library." % f)
            
    
            