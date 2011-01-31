import os

from validator.rdf import RDFParser
from validator.xpi import XPIManager
from validator.errorbundler import ErrorBundle

def _do_test(path, test, failure=True,
             require_install=False, set_type=0,
             listed=False):
    
    package_data = open(path)
    package = XPIManager(package_data, path)
    contents = package.get_file_data()
    err = ErrorBundle()
    if listed:
        err.save_resource("listed", True)
    
    # Populate in the dependencies.
    if set_type:
        err.set_type(set_type) # Conduit test requires type
    if require_install:
        err.save_resource("has_install_rdf", True)
        rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(rdf_data)
        err.save_resource("install_rdf", install_rdf)
    
    test(err, contents, package)
    
    print err.print_summary(verbose=True)
    
    if failure:
        assert err.failed()
    else:
        assert not err.failed()
    
    return err
