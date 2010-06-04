import fnmatch

import decorator


def test_unknown_file(err, filename):
    "Tests some sketchy files that require silly code."
    
    # Extract the file path and the name from the filename
    path = filename.split("/")
    name = path.pop()
    
    if name == "chromelist.txt":
        err.info("Extension contains a deprecated file (%s)" % filename,
                 """The file in question is no longer supported by any
                 modern Mozilla product.""",
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
            err.warning(pattern % (name, extension),
                        "The extension %s is disallowed." % extension,
                        name)
    

@decorator.register_test(tier=2)
def test_targetedapplications(err, package_contents=None,
                              xpi_package=None):
    """Tests to make sure that the targeted applications in the
    install.rdf file are legit and that any associated files (I'm
    looking at you, SeaMonkey) are where they need to be."""
    
    install = err.get_resource("install_rdf")
    
    # Search through the install.rdf document for the SeaMonkey
    # GUID string.
    ta_predicate = install.uri("targetApplication")
    ta_guid_predicate = install.uri("id")
    
    # Isolate all of the bnodes referring to target applications
    for target_app in install.get_objects(None, ta_predicate):
        
        # Get the GUID from the target application
        
        for ta_guid in install.get_objects(target_app,
                                           ta_guid_predicate):
            
            if ta_guid == "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
                
                # Time to test for some install.js
                if not "install.js" in package_contents:
                    err.error("Missing install.js for SeaMonkey.",
                              """SeaMonkey requires install.js, which
                              was not found. install.rdf indicates that
                              the addon supports SeaMonkey.""",
                              "install.rdf")
                    err.reject = True
                
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
        "__MACOSX/*", # I hate them, but there's no way to avoid them.
        "chrome.manifest",
        "chrome/*"]
    whitelisted_extensions = ("txt",)    

    test_layout(err, package_contents, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                "dictionary")
    
    
@decorator.register_test(tier=1, simple=True)
def test_extension_layout(err):
    "Tests the well-formedness of extensions."
    
    if not err.get_resource("has_install_rdf"):
        err.error("Addon missing install.rdf.",
                  "All addons require an install.rdf file.")


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
    whitelisted_files = [
        "chrome/*.jar",
        "__MACOSX/*" # I hate them, but there's no way to avoid them.
        ]
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
    whitelisted_files = [
        "chrome/*.jar",
        "__MACOSX/*" # I hate them, but there's no way to avoid them.
        ]
    whitelisted_extensions = ("manifest", "rdf", "txt", "jar",
                              "png", "gif", "jpg")

    test_layout(err, package_contents, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                "theme")

def test_layout(err, package_contents, mandatory, whitelisted,
                white_extensions, pack_type):
    """Tests the layout of a package. Pass in the various types of files
    and their levels of requirement and this guy will figure out which
    files should and should not be in the package."""
    
    for file_ in package_contents:
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
        if file_.split(".").pop() in white_extensions:
            continue

        # Otherwise, report an error.
        err.error("Unknown file found in %s (%s)" % (pack_type, file_),
                  """Security limitations ban the use of the file %s
                  in this type of addon. Remove the file or use an
                  alternative, supported file format
                  instead.""" % file_,
                  file_)

    # If there's anything left over, it means there's files missing
    if mandatory:
        err.reject = True # Rejection worthy
        for mfile in mandatory:
            err.error("%s missing from %s." % (pack_type, mfile),
                      """%s is a required file for this type of addon.
                      Consult documentation for a full list of required
                      files.""" % mfile)
    