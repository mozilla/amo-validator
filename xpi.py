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
            zf = ZipFile(package)
            
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
        self.zf = zf
        
        
    def get_file_data(self):
        "Returns a dictionary of file information"
        
        # Get a list of ZipInfo objects.
        files = self.zf.infolist()
        
        out_files = {}
        
        # Iterate through each file in the XPI.
        for file in files:
            
            file_doc = {"name": file.filename,
                        "size": file.file_size,
                        "name_lower": file.filename.lower()}
            
            file_doc["extension"] = file_doc["name_lower"].split(".").pop()
            
            out_files[file.filename] = file_doc
        
        return out_files
        
        
        