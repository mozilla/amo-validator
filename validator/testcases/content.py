
from StringIO import StringIO

from validator import decorator
from validator import submain as testendpoint_validator
import validator.testcases.markup.markuptester as testendpoint_markup
import validator.testcases.markup.csstester as testendpoint_css
import validator.testcases.scripting as testendpoint_js
import validator.testcases.langpack as testendpoint_langpack
from validator.xpi import XPIManager
from validator.constants import PACKAGE_LANGPACK, PACKAGE_SUBPACKAGE


@decorator.register_test(tier=2)
def test_packed_packages(err, package_contents=None, xpi_package=None):
    "Tests XPI and JAR files for naughty content."
    
    processed_files = 0
    
    # Iterate each item in the package.
    for name, data in package_contents.items():
        
        if name.startswith("__MACOSX") or \
           name.startswith(".DS_Store"):
            continue
        
        if name.split("/")[-1].startswith("._"):
            err.info(("testcases_content",
                      "test_packed_packages",
                      "macintosh_junk"),
                     "Garbage file found.",
                     ["""A junk file has been detected. It may cause
                      problems with proper operation of the add-on down the
                      road.""",
                      "It is recommended that you delete the file"],
                     name)
        
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
            sub_xpi = XPIManager(package, name, is_subpackage)
            if not sub_xpi.zf:
                err.error(("testcases_content",
                           "test_packed_packages",
                           "jar_subpackage_corrupt"),
                          "Subpackage corrupt.",
                          """The subpackage could not be opened due to
                          issues with corruption. Ensure that the file
                          is valid.""",
                          name)
                continue
            
            temp_contents = sub_xpi.get_file_data()
            
            # Let the error bunder know we're in a sub-package.
            err.push_state(data["name_lower"])
            err.set_type(PACKAGE_SUBPACKAGE) # Subpackage
            testendpoint_validator.test_inner_package(err,
                                                      temp_contents,
                                                      sub_xpi)
            
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
                
            
        elif data["extension"] in ("css", "js"):
            
            try:
                file_data = xpi_package.read(name)
                if not file_data:
                    continue
                
                first_char = ord(file_data[0])
                if first_char > 126 or first_char < 32:
                    file_data = file_data[3:]
                    # Removed: INFO about BOM because it was too frequent.
                
            except KeyError: # pragma: no cover
                _read_error(err, name)
            else:
                if data["extension"] == "css":
                    testendpoint_css.test_css_file(err,
                                                   name,
                                                   file_data)
                elif data["extension"] == "js":
                    testendpoint_js.test_js_file(err,
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
        
        # This aids in creating unit tests.
        processed_files += 1
            
    return processed_files
    

def _read_error(err, name): # pragma: no cover
    """Reports to the user that a file in the archive couldn't be
    read from. Prevents code duplication."""

    err.info(("testcases_content",
              "_read_error",
              "read_error"),
             "File could not be read: %s" % name,
             """A File in the archive could not be read. This may be
             due to corruption or because the path name is too
             long.""",
             name)
