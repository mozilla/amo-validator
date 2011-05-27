import os

from validator.submain import populate_chrome_manifest
from validator.rdf import RDFParser
from validator.xpi import XPIManager
from validator.errorbundler import ErrorBundle

def _do_test(path, test, failure=True,
             require_install=False, set_type=0,
             listed=False, xpi_mode="r"):

    package_data = open(path, "rb")
    package = XPIManager(package_data, mode=xpi_mode, name=path)
    err = ErrorBundle()
    if listed:
        err.save_resource("listed", True)

    # Populate in the dependencies.
    if set_type:
        err.set_type(set_type) # Conduit test requires type
    if require_install:
        err.save_resource("has_install_rdf", True)
        rdf_data = package.read("install.rdf")
        install_rdf = RDFParser(rdf_data)
        err.save_resource("install_rdf", install_rdf)

    populate_chrome_manifest(err, package)

    test(err, package)

    print err.print_summary(verbose=True)

    if failure:
        assert err.failed()
    else:
        assert not err.failed()

    return err


class MockXPI:

    def __init__(self, data=None, subpackage=False):
        if not data:
            data = {}
        self.data = data
        self.subpackage = subpackage

    def test(self):
        return True

    def info(self, name):
        return {"name_lower": name.lower(),
                "extension": name.lower().split(".")[-1]}

    def __iter__(self):
        def i():
            for name in self.data.keys():
                yield name
        return i()

    def __contains__(self, name):
        return name in self.data

    def read(self, name):
        return open(self.data[name]).read()

