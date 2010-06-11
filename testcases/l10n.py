import sys

# Add the path to the lib files we need
sys.path.append('/Users/moco/dev/silme-patched/lib')

from mozilla.core.comparelocales import *
import silme.format

silme.format.Manager.register('dtd', 'properties', 'ini', 'inc')

PACKAGE_ANY = 0
PACKAGE_EXTENSION = 1
PACKAGE_THEME = 2
PACKAGE_DICTIONARY = 3
PACKAGE_LANGPACK = 4
PACKAGE_SEARCHPROV = 5
PACKAGE_MULTI = 1
PACKAGE_SUBPACKAGE = 7


def test_file(path):
    
    optionpack = CompareInit(inipath = path, 
                             inputtype = 'xpi',
                             returnvalue = 'statistics_json')
    
    return compareLocales(optionpack)

@decorator.register_test(tier=2)
def test_xpi(err, package_contents, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness"""
    
    # Skip over incompatible (or unnecessary) package types.
    if err.detected_type in (PACKAGE_ANY,
                             PACKAGE_DICTIONARY,
                             PACKAGE_SEARCHPROV,
                             PACKAGE_SUBPACKAGE):
        # NOTE : Should we do this with PACKAGE_MULTI?
        return
    
    test_file(xpi_package.filename)
    