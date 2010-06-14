import sys
import os

import json
from StringIO import StringIO

import decorator

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

# The threshold that determines the number of entities that must not be
# missing from the package.
L10N_THRESHOLD = 0.10


def test_file(err, path):
    
    optionpack = CompareInit(inipath = path, 
                             inputtype = 'xpi',
                             returnvalue = 'statistics_json')
    
    stdout = sys.stdout
    sys.stdout = StringIO.StringIO()
    
    compareLocales(optionpack)
    
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    
    output_parsed = json.loads(output)
    
    if not isinstance(output_parsed, list):
        err.info("L10n library produced mysterious results.",
                 """We expected a list coming out of the L10n stuff,
                 but we got something else. Not really sure what it
                 means.""")
        return None
    else:
        return output_parsed
    

@decorator.register_test(tier=2)
def test_xpi(err, package_contents, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness"""
    
    # Skip over incompatible (or unnecessary) package types.
    if err.detected_type in (PACKAGE_ANY,
                             PACKAGE_DICTIONARY,
                             PACKAGE_SEARCHPROV,
                             PACKAGE_SUBPACKAGE) or \
       err.is_nested_package():
        # NOTE : Should we do also this with PACKAGE_MULTI?
        return
    
    path = xpi_package.filename
    path = os.path.realpath(path)
    
    data = test_file(err, path)
    
    if not data:
        return
    else:
        
        unmod_pattern = \
            "The %s locale contains %d unmodified translations."
        missing_pattern = "The %s locale is missing %d entities."
        missing_file_pattern = "The %s locale is missing %d files."
        
        for child in data:
            children_obj = child["children"]
            name = children_obj[0]
            stats = children_obj[1]["children"][0]
            
            total_entities = int(stats["total"])
            
            if "unmodifiedEntities" in stats:
                unmodified_entities = int(stats["unmodifiedEntities"])
                unmodified_ratio = unmodified_entities / total_entities
                if unmodified_ratio > \
                   L10N_THRESHOLD:
                    err.warning(unmod_pattern % (name,
                                                 unmodified_entities),
                                """The number of unmodified entities
                                must not exceed a %d ratio.""" %
                                unmodified_ratio)
            
            if "missingEntities" in stats:
                missing_entities = int(stats["missingEntities"])
                err.warning(missing_pattern % (name, missing_entities),
                            """There should not be missing entities in
                            any given locale.""")
            
            if "missingEntitiesInMissingFiles" in stats and \
               "missingEntities" in stats:
                missing_files = \
                    int(stats["missingEntitiesInMissingFiles"])
                err.warning(missing_pattern % (name, missing_files),
                            """Locales should include all locale
                            files.""")
            
    