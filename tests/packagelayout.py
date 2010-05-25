import fnmatch

import rdflib
from rdflib import URIRef

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

def test_targetedapplications(eb, package_contents={},
                              xpi_package=None):
    """Tests to make sure that the targeted applications in the
    install.rdf file are legit and that any associated files (I'm
    looking at you, SeaMonkey) are where they need to be."""
    
    print "Validating target application support..."
    
    # If there isn't an install.rdf, we can't test for SeaMonkey
    # support. Boo hoo.
    
    if not eb.get_resource("has_install_rdf"):
        return eb
    
    rdf = eb.get_resource("install_rdf")
    rdfDoc = rdf.rdf
    
    # Search through the install.rdf document for the SeaMonkey
    # GUID string.
    ta_predicate = \
        URIRef("http://www.mozilla.org/2004/em-rdf#targetApplication")
    ta_guid_predicate = \
        URIRef("http://www.mozilla.org/2004/em-rdf#id")
    
    # Isolate all of the bnodes referring to target applications
    for ta in rdfDoc.objects(None, ta_predicate):
        
        # Get the GUID from the target application
        
        for ta_guid in rdfDoc.objects(ta, ta_guid_predicate):
            
            if ta_guid == "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
                print "We found some SeaMonkey."
                
                # Time to test for some install.js
                if not "install.js" in package_contents:
                    eb.error("SeaMonkey support found, but missing install.js.")
                    eb.reject = True
                
                break
    
    
    return eb
    

def test_dictionary_layout(eb, package_contents={}, xpi_package=None):
    """Ensures that dictionary packages contain the necessary
    components and that there are no other extraneous files lying
    around."""
    
    print "Testing dictionary package layout..."
    
    # Define rules for the structure.
    mandatory_files = [
        "install.rdf",
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
    
    # If there's anything left over, it means there's files missing
    if mandatory_files:
        eb.reject = True # Rejection worthy
        for mfile in mandatory_files:
            eb.error("%s missing from dictionary." % mfile)
    
    return eb

# Register the tests with the decorator.
decorator.register_test(1, test_blacklisted_files)
decorator.register_test(1, test_dictionary_layout, 3) # dictionaries
decorator.register_test(2, test_targetedapplications, 3)

