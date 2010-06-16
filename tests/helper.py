import os

from rdf import RDFParser
from xpi import XPIManager
from errorbundler import ErrorBundle

def _do_test(path, test, failure=True,
             require_install=False, set_type=0):
    
    package_data = open(path)
    package = XPIManager(package_data, path)
    contents = package.get_file_data()
    err = ErrorBundle(None, True)
    
    # Populate in the dependencies.
    if set_type:
        err.set_type(1) # Conduit test requires type
    if require_install:
        err.save_resource("has_install_rdf", True)
        rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(rdf_data)
        err.save_resource("install_rdf", install_rdf)
    
    test(err, contents, package)
    
    err.print_summary()
    
    if failure:
        assert err.failed()
    else:
        assert not err.failed()