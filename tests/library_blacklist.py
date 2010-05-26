import os

import hashlib

import decorator

@decorator.register_test(tier=1)
def test_library_blacklist(eb, package_contents={}, xpi_package=None):
    """Test to make sure that the user isn't trying to sneak a JS
    library into their XPI. This tests for:
    - All jQuery
    - All Prototype
    - Most SWFObject
    - Some MooTools
    - Some dojo"""
    
    # Generate a tuple of definition data
    definitions = tuple(open("hashes.txt").readlines())
    
    # Iterate each file
    for f in package_contents:
        # Open and hash the file
        data = xpi_package.zf.read(f)
        h = hashlib.sha1(data).hexdigest()
        
        # Test if the file is blocked
        if h in definitions:
            eb.error("File (%s) is a blacklisted JS library." % f)
            
