import zipfile
from zipfile import ZipFile

class XPIManager(object):
    """An XPI reader and management class. Allows fun things like
    reading, listing, and extracting files from an XPI without you
    needing to worry about things like zip files or IO."""
    
    
    def __init__(self, package, name=None, subpackage=False):
        "Create a new managed XPI package"
        
        self.zf = None
        
        # Try opening the XPI as a zip.
        try:
            zip_package = ZipFile(package)
            
        except:
            # Pokemon error handling here is unnecessary. If we can't open
            # it, we can't open it. We shouldn't be the "why won't the add-on
            # open" brigade.
            return
        
        # Store away the filename for future use.
        self.filename = name or package
        self.extension = self.filename.split(".")[-1]
        self.subpackage = subpackage
        
        # Save the reference to the XPI to memory
        self.zf = zip_package
        
    def test(self):
        """Tests the validity and non-corruptness of the zip.
        
        Will return true on failure."""
        
        # This guy tests the hashes of the content.
        try:
            output = self.zf.testzip()
            return output is not None
        except:
            return True
        
    def get_file_data(self):
        "Returns a dictionary of file information"
        
        # Get a list of ZipInfo objects.
        files = self.zf.infolist()
        out_files = {}
        
        # Iterate through each file in the XPI.
        for file_ in files:
            
            file_doc = {"name": file_.filename,
                        "size": file_.file_size,
                        "name_lower": file_.filename.lower()}
            
            file_doc["extension"] = file_doc["name_lower"].split(".")[-1]
            
            out_files[file_.filename] = file_doc
        
        return out_files
        
    def read(self, filename):
        "Reads a file from the archive and returns a string."
        
        data = self.zf.read(filename)
        
        return data
        
