import fnmatch

import decorator
import xpi

def test_blacklisted_files(eb, package_contents={}, xpi_package=None):
    "Detects blacklisted files and extensions."
    
    print "Testing package against extension blacklist..."
    
    # Detect blacklisted files based on their extension.
    blacklisted_extensions = ("dll", "exe", "dylib", "so",
                              "sh", "class", "swf")
    
    pattern = "File '%s' is using a blacklisted file extension (%s)"
    for name, file_ in package_contents.items():
        # Simple test to ensure that the extension isn't blacklisted
        if file_["extension"] in blacklisted_extensions:
            eb.warning(pattern % (name, file_["extension"]))
    
    return eb

def test_targetedapplications(eb, package_contents={}, xpi_package=None):
    """Tests to make sure that the targeted applications in the
    install.rdf file are legit and that any associated files (I'm looking
    at you, SeaMonkey) are where they need to be."""
    
    

def test_dictionary_layout(eb, package_contents={}, xpi_package=None):
    """Ensures that dictionary packages contain the necessary
    components and that there are no other extraneous files lying
    around."""
    
    print "Testing dictionary package layout..."
    
    # Define rules for the structure.
    mandatory_files = [
        "install.rdf",
        "dictionaries/",
        "dictionaries/*.aff",
        "dictionaries/*.dic"]
    whitelisted_files = [
        "install.js",
        "__MACOSX/*", # I hate them, but there's no way to avoid them.
        "chrome.manifest",
        "chrome/*"]
    whitelisted_extensions = ("txt",)
    
    for file_ in package_contents:
        # Remove the file from the mandatory file list.
        #if file_ in mandatory_files:
        mfile_list = \
             [mf for mf in mandatory_files if fnmatch.fnmatch(file_, mf)]
        if mfile_list:
            # Isolate the mandatory file pattern and remove it.
            mfile = mfile_list[0]
            mandatory_files.remove(mfile)
            continue
        
        # Remove the file from the whitelist.
        if any(fnmatch.fnmatch(file_, wlfile) for wlfile in
               whitelisted_files):
            continue
    
        # Is it a directory?
        if file_.endswith("/"):
            continue
        
        # Is it a whitelisted file type?
        if file_.split(".").pop() in whitelisted_extensions:
            continue
        
        # Otherwise, report an error.
        eb.error("Unknown file found in dictionary (%s)" % file_)
    
    return eb


# Register the tests with the decorator.
decorator.register_test(1, test_blacklisted_files)
decorator.register_test(1, test_dictionary_layout, 3) # for dictionaries

