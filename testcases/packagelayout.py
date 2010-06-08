import fnmatch
from rdflib import BNode

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
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    # Search through the install.rdf document for the SeaMonkey
    # GUID string.
    ta_predicate = install.uri("targetApplication")
    ta_guid_predicate = install.uri("id")
    
    used_targets = [];
    
    # Isolate all of the bnodes referring to target applications
    for target_app in install.get_objects(None, ta_predicate):
        
        # Get the GUID from the target application
        
        for ta_guid in install.get_objects(target_app,
                                           ta_guid_predicate):
            
            used_targets.append(ta_guid)
            
            if ta_guid == "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
                
                # Time to test for some install.js
                if not "install.js" in package_contents:
                    err.warning("Missing install.js for SeaMonkey.",
                                """SeaMonkey requires install.js, which
                                was not found. install.rdf indicates
                                that the addon supports SeaMonkey.""",
                                "install.rdf")
                    err.reject = True
                
                break
    
    no_duplicate_targets = set(used_targets)
    
    if len(used_targets) != len(no_duplicate_targets):
        err.warning("Found duplicate <em:targetApplication> elements.",
                    """Multiple targetApplication elements were found
                    in the install.manifest file that refer to the same
                    application GUID. There should not be duplicate
                    target applications entries.""",
                    "install.rdf")
    

@decorator.register_test(tier=1)
def test_install_rdf_params(err, package_contents=None,
                            xpi_package=None):
    """Tests to make sure that some of the values in install.rdf
    are not gummed up."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    if err.get_resource("listed"):
        shouldnt_exist = ("hidden")
    else:
        shouldnt_exist = ("updateURL",
                          "updateKey",
                          "hidden")
    obsolete = ("file")
    must_exist_once = ["id_",
                       "version",
                       "name",
                       "targetApplication"]
    may_exist_once = ["about", # For <Description> element
                      "type",
                      "optionsURL",
                      "aboutURL",
                      "iconURL",
                      "homepageURL",
                      "creator"]
    may_exist = ("targetApplication",
                 "localized",
                 "description",
                 "creator",
                 "translator",
                 "contributor",
                 "targetPlatform",
                 "requires",
                 "developer")
    
    banned_pattern = "Banned element %s exists in install.rdf."
    obsolete_pattern = "Obsolete element %s found in install.rdf."
    unrecognized_pattern = "Unrecognized element in install.rdf: %s"
    
    top_id = install.get_root_subject()
    
    for pred_raw in install.rdf.predicates(top_id, None):
        predicate = pred_raw.split("#").pop()
        
        # Some of the element names collide with built-in function
        # names of tuples/lists.
        if predicate == "id":
            predicate += "_"
        
        # Test if the predicate is banned
        if predicate in shouldnt_exist:
            err.error(banned_pattern % predicate,
                      """The detected element is not allowed in addons
                      under the configuration that you've specified."""
                      "install.rdf")
            continue
        
        # Test if the predicate is obsolete
        if predicate in obsolete:
            err.info(obsolete_pattern % predicate,
                     """The found element has not been banned, but it
                     is no longer supported by any modern Mozilla
                     product. Removing the element is recommended and
                     will not break support.""",
                     "install.rdf")
            continue
        
        # Remove the predicate from move_exist_once if it's there.
        if predicate in must_exist_once:
            must_exist_once.remove(predicate)
            continue
        
        # Do the same for may_exist_once.
        if predicate in may_exist_once:
            may_exist_once.remove(predicate)
            continue
        
        # If the element is safe for repetition, continue
        if predicate in may_exist:
            continue
        
        # If the predicate isn't in any of the above lists, it is
        # invalid and needs to go.
        err.error(unrecognized_pattern % predicate,
                  """The element that was found is not a part of the
                  install manifest specification, has been used too
                  many times, or is not applicable to the current
                  configuration.""",
                  "install.rdf")
        
    # Once all of the predicates have been tested, make sure there are
    # no mandatory elements that haven't been found.
    if must_exist_once:
        for predicate in must_exist_once:
            err.error("install.rdf is missing element: %s" % predicate,
                      """The element listed is a required element in
                      the install manifest specification. It must be
                      added to your addon.""",
                      "install.rdf")
    

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
    
    
@decorator.register_test(tier=1)
def test_extension_layout(err, package_contents, xpi_package):
    "Tests the well-formedness of extensions."
    
    # Subpackages don't need to be tested for install.rdf
    if xpi_package.subpackage:
        return
    
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
    