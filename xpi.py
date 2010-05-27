import zipfile
from zipfile import ZipFile

class XPIManager:
    """An XPI reader and management class. Allows fun things like
    reading, listing, and extracting files from an XPI without you
    needing to worry about things like zip files or IO."""
    
    
    def __init__(self, package):
        "Create a new managed XPI package"
        
        # Store away the filename for future use.
        self.filename = package
        self.extension = package.split(".").pop()
        
        # Try opening the XPI as a zip.
        try:
            zip_package = ZipFile(package)
            
        except zipfile.BadZipfile:
            # The XPI is corrupt or invalid.
            print "The XPI is invalid."
            raise
            
        except IOError:
            print "Package was not found."
            raise
            
        except:
            print "Something strange and deathly happened to the XPI."
            raise
        
        # Save the reference to the XPI to memory
        self.zf = zip_package
        
    def test(self):
        "Tests the validity and non-corruptness of the zip."
        
        # This guy tests the hashes of the content.
        output = self.zf.testzip()
        return output is None
        
        
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
            
            file_doc["extension"] = file_doc["name_lower"].split(".").pop()
            
            out_files[file_.filename] = file_doc
        
        return out_files
        
    def read(self, filename):
        "Reads a file from the archive and returns a string."
        
        data = self.zf.read(filename)
        
        return data
        
