import hashlib

import decorator

@decorator.register_test(tier=1)
def test_library_blacklist(err, package_contents=None, xpi_package=None):
    """Test to make sure that the user isn't trying to sneak a JS
    library into their XPI. This tests for:
    - All jQuery
    - All Prototype
    - Most SWFObject
    - Some MooTools
    - Some dojo
    
    The hash definitions file that is used by this test can easily be
    generated using the libhasher.py tool."""
    
    # Generate a tuple of definition data
    lines = open("hashes.txt").readlines()
    definitions = [line.strip() for line in lines]
    
    # Iterate each file
    for file_ in package_contents:
        # Open and hash the file
        data = xpi_package.read(file_)
        hash_ = hashlib.sha1(data).hexdigest()
        
        # Test if the file is blocked
        if hash_ in definitions:
            err.error("File (%s) is a blacklisted JS library." % file_,
                      """JavaScript libraries are not permitted within
                      Firefox addons. Consider modifying your code to
                      run without the aid of the library in
                      question.""",
                      file_)
            
