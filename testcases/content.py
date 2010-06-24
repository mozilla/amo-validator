
from StringIO import StringIO

import decorator
import validator as testendpoint_validator
import testcases.markup.markuptester as testendpoint_markup
import testcases.markup.csstester as testendpoint_css
import testcases.langpack as testendpoint_langpack
from xpi import XPIManager
from constants import PACKAGE_LANGPACK, PACKAGE_SUBPACKAGE


@decorator.register_test(tier=2)
def test_packed_packages(err, package_contents=None, xpi_package=None):
    "Tests XPI and JAR files for naughty content."
    
    processed_files = 0
    
    # Iterate each item in the package.
    for name, data in package_contents.items():
        
        if name.startswith("__MACOSX") or \
           name.startswith(".DS_Store"):
            continue
        
        processed = False
        
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
            try:
                sxpi_package = XPIManager(package, name, is_subpackage)
            except Exception as error:
                err.error("Subpackage %s is corrupt." % name,
                          """The subpackage could not be opened due to
                          issues with corruption. Ensure that the file
                          is valid.""")
                continue
            
            package_contents = sxpi_package.get_file_data()
            
            # Let the error bunder know we're in a sub-package.
            err.push_state(data["name_lower"])
            err.set_type(PACKAGE_SUBPACKAGE) # Subpackage
            testendpoint_validator.test_inner_package(err,
                                                      package_contents,
                                                      sxpi_package)
            
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
            testendpoint_validator.test_package(err, package, name)
            
            package.close()
            err.pop_state()
            
        elif data["extension"] in ("xul", "xml", "html", "xhtml"):
            
            try:
                file_data = xpi_package.read(name)
            except KeyError: # pragma: no cover
                _read_error(err, name)
            else:
                parser = testendpoint_markup.MarkupParser(err)
                parser.process(name,
                               file_data,
                               data["extension"])
                
                processed = True
                
            
        elif data["extension"] == "css":
            
            try:
                file_data = xpi_package.read(name)
            except KeyError: # pragma: no cover
                _read_error(err, name)
            else:
                testendpoint_css.test_css_file(err,
                                               name,
                                               file_data)
                                                         
        
        # This is tested in test_langpack.py
        if err.detected_type == PACKAGE_LANGPACK and not processed:
            
            try:
                file_data = xpi_package.read(name)
            except KeyError: # pragma: no cover
                _read_error(err, name)
            else:
                testendpoint_langpack.test_unsafe_html(err,
                                                       name,
                                                       file_data)
        
        # This aids in testing.
        processed_files += 1
            
    return processed_files
    

def _read_error(err, name): # pragma: no cover
    """Reports to the user that a file in the archive couldn't be
    read from. Prevents code duplication."""

    err.info("File could not be read: %s" % name,
             """A File in the archive could not be read. This may be
             due to corruption or because the path name is too
             long.""",
             name)
