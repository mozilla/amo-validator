import re

from rdflib import Graph
from StringIO import StringIO

import decorator
import validator
from xpi import XPIManager

@decorator.register_test(tier=1)
def test_hidden(err, package_contents=None, xpi_package=None):
    """Test to check for the now-obsolete <em:hidden> element in the
    install.rdf file. This attribute has been obsoleted because users
    may have difficulty determining if an addon is installed or not."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    ta_hidden_predicate = install.uri("hidden")
    
    hidden_object = install.get_object(None, ta_hidden_predicate)
    
    if hidden_object is not None:
        err.warning("install.rdf contains <em:hidden> element",
                    """The <em:hidden> element is obsoleted in Firefox
                    version 3.6 and up because it increases difficulty
                    for users attempting to determine whether they have
                    a particular extension installed or attempting to
                    uninstall said extensions.""",
                    "install.rdf")
    

@decorator.register_test(tier=2)
def test_packed_packages(err, package_contents=None, xpi_package=None):
    "Tests XPI and JAR files for naughty content."
    
    # Iterate each item in the package.
    for name, data in package_contents.items():
        
        if name.startswith("__MACOSX"):
            continue
        
        # If that item is a container file, unzip it and scan it.
        if data["extension"] == "jar":
            
            # Unpack the package and load it up.
            package = StringIO(xpi_package.read(name))
            xpi_package = XPIManager(package, name)
            
            if not xpi_package.test():
                err.error("Subpackage %s is corrupt." % name,
                          """The subpackage could not be opened due to
                          issues with corruption. Ensure that the file
                          is valid.""")
                continue
            
            package_contents = xpi_package.get_file_data()
            
            # Let the error bunder know we're in a sub-package.
            err.push_state(data["name_lower"])
            err.set_type(7) # Subpackage
            validator.test_inner_package(err,
                package_contents, xpi_package)
            
            package.close()
            err.pop_state()
            
        elif data["extension"] == "xpi":
            
            # Unpack!
            package = StringIO(xpi_package.read(name))
            
            err.push_state(data["name_lower"])
            
            # There are no expected types for packages within a multi-
            # item package.
            validator.test_package(err, package, name)
            
            package.close()
            err.pop_state()
