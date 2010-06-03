import os

import decorator
import testcases
import testcases.library_blacklist
from errorbundler import ErrorBundle
from xpi import XPIManager
from rdf import RDFParser


def test_blacklisted_files():
    """Tests the validator's ability to hash each individual file and
    (based on this information) determine whether the addon passes or
    fails the validation process."""
    
    package_data = open("tests/resources/libraryblacklist/blocked.xpi")
    package = XPIManager(package_data, "blocked.xpi")
    contents = package.get_file_data()
    err = ErrorBundle(None, True)
    
    testcases.library_blacklist.test_library_blacklist(err,
                                                       contents,
                                                       package)
    
    err.print_summary()
    
    assert err.failed()