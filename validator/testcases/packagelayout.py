import fnmatch

from validator import decorator


def test_unknown_file(err, filename):
    "Tests some sketchy files that require silly code."
    
    # Extract the file path and the name from the filename
    path = filename.split("/")
    name = path.pop()
    
    if name == "chromelist.txt":
        err.info(("testcases_packagelayout",
                  "test_unknown_file",
                  "deprecated_file"),
                 "Extension contains a deprecated file",
                 """The file "%s" is no longer supported by any
                 modern Mozilla product.""" % filename,
                 filename)
        return True


@decorator.register_test(tier=1)
def test_blacklisted_files(err, package_contents=None, xpi_package=None):
    "Detects blacklisted files and extensions."
    
    # Detect blacklisted files based on their extension.
    blacklisted_extensions = ("dll", "exe", "dylib", "so",
                              "sh", "class", "swf")
    
    pattern = "File '%s' is using a blacklisted file extension (%s)"
    for name, file_ in package_contents.items():
        # Simple test to ensure that the extension isn't blacklisted
        extension = file_["extension"]
        if extension in blacklisted_extensions:
            err.warning(("testcases_packagelayout",
                         "test_blacklisted_files",
                         "disallowed_extension"),
                        "Blacklisted file extension found",
                        ["""The file "%s" uses a blacklisted file
                         extension.""" % name,
                         "The extension %s is disallowed." % extension],
                        name)

@decorator.register_test(tier=1)
def test_layout_all(err, package_contents, xpi_package):
    "Tests the well-formedness of extensions."
    
    # Subpackages don't need to be tested for install.rdf.
    if xpi_package.subpackage:
        return
    
    if not err.get_resource("has_install_rdf"):
        err.error(("testcases_packagelayout",
                  "test_layout_all",
                  "missing_install_rdf"),
                 "Addon missing install.rdf.",
                  "All addons require an install.rdf file.")
    

@decorator.register_test(tier=2)
def test_xpcom(err, package_contents, xpi_package):
    "Test to make sure XPCOM is not used for FF4+"
    
    if not err.get_resource("ff4"):
        return None
    
    # Test for XPCOM incompatibility.
    for name, file_ in package_contents.items():
        
        if name.startswith("components/"):
            err.warning(("testcases_packagelayout",
                         "test_xpcom",
                         "incompatible_xpcom_detected"),
                        "XPCOM ties detected",
                        ["""Files were found in the /components/ directory,
                         which generally indicates XPCOM references. Firefox
                         4 no longer supports XPCOM. This interface is
                         subject to change.""",
                         'File "%s" represents XPCOM ties.' % name],
                        name);
            break
        
    

@decorator.register_test(tier=1, expected_type=3)
def test_dictionary_layout(err, package_contents=None, xpi_package=None):
    """Ensures that dictionary packages contain the necessary
    components and that there are no other extraneous files lying
    around."""
    
    # Define rules for the structure.
    mandatory_files = [
        "install.rdf",
        "dictionaries/*.aff",
        "dictionaries/*.dic"]
    whitelisted_files = [
        "install.js",
        "dictionaries/*.aff", # List again because there must >0
        "dictionaries/*.dic",
        "chrome.manifest",
        "chrome/*"]
    whitelisted_extensions = ("txt",)    

    test_layout(err, package_contents, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                "dictionary")
    

@decorator.register_test(tier=1, expected_type=4)
def test_langpack_layout(err, package_contents=None, xpi_package=None):
    """Ensures that language packs only contain exactly what they
    need and nothing more. Otherwise, somebody could sneak something
    sneaking into them."""

    # Define rules for the structure.
    mandatory_files = [
        "install.rdf",
        "chrome/*.jar",
        "chrome.manifest"]
    whitelisted_files = ["chrome/*.jar"]
    whitelisted_extensions = ("manifest", "rdf", "jar", "dtd",
                              "properties", "xhtml", "css")
    
    test_layout(err, package_contents, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                "language pack")


@decorator.register_test(tier=1, expected_type=2)
def test_theme_layout(err, package_contents=None, xpi_package=None):
    """Ensures that themes only contain exactly what they need and
    nothing more. Otherwise, somebody could sneak something sneaking
    into them."""

    # Define rules for the structure.
    mandatory_files = [
        "install.rdf",
        "chrome/*.jar",
        "chrome.manifest"]
    whitelisted_files = ["chrome/*.jar"]
    whitelisted_extensions = ("manifest", "rdf", "txt", "jar",
                              "png", "gif", "jpg")

    test_layout(err, package_contents, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                "theme")

def test_layout(err, package_contents, mandatory, whitelisted,
                white_extensions=None, pack_type="Unknown Addon"):
    """Tests the layout of a package. Pass in the various types of files
    and their levels of requirement and this guy will figure out which
    files should and should not be in the package."""
    
    for file_ in package_contents:
        
        if fnmatch.fnmatch(file_, "__MACOSX/*") or \
           fnmatch.fnmatch(file_, ".DS_Store"):
            continue
        
        # Remove the file from the mandatory file list.
        #if file_ in mandatory_files:
        mfile_list = \
             [mf for mf in mandatory if fnmatch.fnmatch(file_, mf)]
        if mfile_list:
            # Isolate the mandatory file pattern and remove it.
            mfile = mfile_list[0]
            mandatory.remove(mfile)
            continue

        # Test if the file is in the whitelist.
        if any(fnmatch.fnmatch(file_, wlfile) for wlfile in
               whitelisted):
            continue

        # Is it a directory?
        if file_.endswith("/"):
            continue

        # Is the file a sketch file?
        if test_unknown_file(err, file_):
            continue

        # Is it a whitelisted file type?
        if file_.split(".")[-1] in white_extensions:
            continue

        # Otherwise, report an error.
        err.error(("testcases_packagelayout",
                   "test_layout",
                   "unknown_file"),
                  "Unknown file found in add-on",
                  ["""Security limitations ban the use of the detected file
                   in this type of addon. Remove the file or use an
                   alternative, supported file format
                   instead.""",
                   "%s add-ons cannot contain files like %s" % (pack_type,
                                                                file_)],
                  file_)

    # If there's anything left over, it means there's files missing
    if mandatory:
        err.reject = True # Rejection worthy
        for mfile in mandatory:
            err.error(("testcases_packagelayout",
                       "test_layout",
                       "missing_required"),
                      "Required file missing",
                      ["""The add-on requires certain files. Consult the
                       documentation for a full list of required files.""",
                       'Add-ons of type "%s" require "%s"' % (mfile,
                                                              pack_type)])
