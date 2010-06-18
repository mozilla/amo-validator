import sys
import os

import json
from StringIO import StringIO

import decorator
from constants import *

# Add the path to the lib files we need
sys.path.append('/Users/moco/dev/silme/lib')

from mozilla.core.comparelocales import *
import silme.format

silme.format.Manager.register('dtd', 'properties', 'ini', 'inc')

# The threshold that determines the number of entities that must not be
# missing from the package.
L10N_THRESHOLD = 0.10


def _test_file(err, optionpack):
    "Runs the L10n tests against an addon package."
    
    stdout = sys.stdout
    sys.stdout = StringIO.StringIO()
    
    compareLocales(optionpack)
    
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    
    output = output.strip()
    
    if not output or output.startswith(("WARNING", "ERROR")):
        err.info("This extension appears not to be localized.",
                 """The package does not contain any localization
                 support.""")
        return None
    
    output_parsed = json.loads(output)
    
    if not isinstance(output_parsed, list):
        err.info("L10n library produced mysterious results.",
                 """We expected a list coming out of the L10n stuff,
                 but we got something else. Not really sure what it
                 means.""")
        return None
    else:
        return output_parsed
    

@decorator.register_test(tier=3)
def test_xpi(err, package_contents, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness"""
    
    # Skip over incompatible (or unnecessary) package types.
    if err.detected_type in (PACKAGE_LANGPACK, # Handled seperately.
                             PACKAGE_ANY,
                             PACKAGE_DICTIONARY,
                             PACKAGE_SEARCHPROV,
                             PACKAGE_SUBPACKAGE) or \
       err.is_nested_package():
        # NOTE : Should we also do this with PACKAGE_MULTI?
        return
    
    path = xpi_package.filename
    path = os.path.realpath(path)
    
    optionpack = CompareInit(inipath = path, 
                             inputtype = 'xpi',
                             returnvalue = 'statistics_json')
    
    data = _test_file(err, optionpack)
    _process_results(err, data)
    

@decorator.register_test(tier=3, expected_type=PACKAGE_LANGPACK)
def test_lp_xpi(err, package_contents, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness """
    
    optionpack = CompareInit(inputtype = 'xpis',
                             returnvalue = 'statistics_json',
                             locales=[])
    
    path = xpi_package.filename
    path = os.path.realpath(path)
    
    # Tell the option pack which file we're validating.
    # We need to set a reference package. The reference packages are in
    # langpacks/ and are named like (appname).en-US.jar. We just want
    # the first compatible app, though, so just use the first target
    # application we can find.
    optionpack.inipath = ("langpacks/%s.xpi" %
                            err.get_resource("supports")[0],
                          path)
    optionpack.l10nbase = ("chrome/en-US.jar!locale/en-US/",
                           "chrome/en-US.jar!locale/en-US/")
    
    data = _test_file(err, optionpack)
    _process_results(err, data)
    

def _process_results(err, data):
    
    if not data:
        return
    
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
            
            if unmodified_ratio > L10N_THRESHOLD:
                err.warning(unmod_pattern % (name, 
                                             unmodified_entities),
                            """The number of unmodified entities should
                            usually not exceed a %f ratio.""" %
                            L10N_THRESHOLD)
        
        if "missingEntities" in stats:
            missing_entities = int(stats["missingEntities"])
            err.warning(missing_pattern % (name, missing_entities),
                        """There should not be missing entities in any
                        given locale.""")
        
        if "missingEntitiesInMissingFiles" in stats and \
           "missingFiles" in stats:
            missing_files = int(stats["missingFiles"])
            err.warning(missing_file_pattern % (name, missing_files),
                        """Certain files that are present in the
                        reference locale (i.e.: en-US) are not present
                        in the %s locale.""" % name)
        
