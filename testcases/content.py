import re

from rdflib import Graph
from StringIO import StringIO

import decorator
import validator
import testcases.markup.markuptester
import testcases.langpack
from xpi import XPIManager

PACKAGE_ANY = 0
PACKAGE_EXTENSION = 1
PACKAGE_THEME = 2
PACKAGE_DICTIONARY = 3
PACKAGE_LANGPACK = 4
PACKAGE_SEARCHPROV = 5
PACKAGE_MULTI = 1
PACKAGE_SUBPACKAGE = 7

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
            # This is either a subpackage or a nested theme.
            
            # Whether this is a subpackage or a nested theme is
            # determined by whether it is in the root folder or not.
            # Subpackages are always found in a directory such as
            # /chrome or /content.
            is_subpackage = name.count("/") > 0
            
            # Unpack the package and load it up.
            package = StringIO(xpi_package.read(name))
            xpi_package = XPIManager(package, name, is_subpackage)
            
            if not xpi_package.test():
                err.error("Subpackage %s is corrupt." % name,
                          """The subpackage could not be opened due to
                          issues with corruption. Ensure that the file
                          is valid.""")
                continue
            
            package_contents = xpi_package.get_file_data()
            
            # Let the error bunder know we're in a sub-package.
            err.push_state(data["name_lower"])
            err.set_type(PACKAGE_SUBPACKAGE) # Subpackage
            validator.test_inner_package(err,
                package_contents, xpi_package)
            
            package.close()
            err.pop_state()
            
        elif data["extension"] == "xpi":
            # It's not a subpackage, it's a nested extension. These are
            # found in multi-extension packages.
            
            # Unpack!
            package = StringIO(xpi_package.read(name))
            
            err.push_state(data["name_lower"])
            
            # There are no expected types for packages within a multi-
            # item package.
            validator.test_package(err, package, name)
            
            package.close()
            err.pop_state()
            
        elif data["extension"] in ("xul", "xml", "html", "xhtml"):
            
            parser = testcases.markup.markuptester.MarkupParser(err)
            parser.process(name,
                           xpi_package.read(name),
                           data["extension"])
            
        elif data["extension"] in ("dtd", "properties") and \
             err.detected_type == PACKAGE_LANGPACK:
            
            data = xpi_package.read(name)
            testcases.langpack._test_unsafe_html(err, name, data)
            
