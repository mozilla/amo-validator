from zipfile import ZipFile
from StringIO import StringIO


def to_utf8(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return s


class XPIManager(object):
    """
    An XPI reader and management class. Allows fun things like reading,
    listing, and extracting files from an XPI without you needing to
    worry about things like zip files or IO.
    """

    def __init__(self, package, mode='r', name=None, subpackage=False):
        'Create a new managed XPI package'

        self.zf = ZipFile(package, mode=mode)

        # Store away the filename for future use.
        self.filename = name or package
        self.extension = self.filename.split('.')[-1]
        self.subpackage = subpackage

        self.contents_cache = None

    def __iter__(self):
        return (name for name in self.zf.namelist())

    def __contains__(self, item):
        return item in self.zf.namelist()

    def info(self, name):
        """Get info on a single file."""
        return self.package_contents()[name]

    def package_contents(self):
        'Returns a dictionary of file information'

        if self.contents_cache:
            return self.contents_cache

        # Get a list of ZipInfo objects.
        files = self.zf.infolist()
        out_files = {}

        # Iterate through each file in the XPI.
        for file_ in files:

            file_doc = {'name': file_.filename,
                        'size': file_.file_size,
                        'name_lower': file_.filename.lower()}

            file_doc['extension'] = file_doc['name_lower'].split('.')[-1]

            out_files[file_.filename] = file_doc

        self.contents_cache = out_files
        return out_files

    def read(self, filename):
        'Reads a file from the archive and returns a string.'

        data = self.zf.read(filename)
        return data

    def write(self, name, data):
        """Write a blob of data to the XPI manager."""
        if isinstance(data, StringIO):
            self.zf.writestr(name, data.getvalue())
        else:
            self.zf.writestr(name, to_utf8(data))

    def write_file(self, name, path=None):
        """Write the contents of a file from the disk to the XPI."""

        if path is None:
            path = name

        self.zf.write(path, name)
