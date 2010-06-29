import sys
import os

import json
from StringIO import StringIO

import decorator
from chromemanifest import ChromeManifest
from xpi import XPIManager
from constants import PACKAGE_EXTENSION, \
                      PACKAGE_THEME, \
                      PACKAGE_LANGPACK

import testcases.l10n.dtd
import testcases.l10n.properties

# Add the path to the lib files we need
sys.path.append('/Users/moco/dev/silme/lib')

# pylint: disable-msg=F0401,W0613
from mozilla.core.comparelocales import compareLocales, CompareInit
import silme.format

silme.format.Manager.register('dtd', 'properties', 'ini', 'inc')

# The threshold that determines the number of entities that must not be
# missing from the package.
L10N_THRESHOLD = 0.10

def _test_file(err, optionpack):
    "Runs the L10n tests against an addon package."
    
    stdout = sys.stdout
    sys.stdout = StringIO()
    
    compareLocales(optionpack)
    
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    
    output = output.strip()
    print output
    
    if not output or output.startswith(("WARNING", "ERROR")):
        err.info("This extension appears not to be localized.",
                 """The package does not contain any localization
                 support.""")
        return None
    
    output_parsed = json.loads(output)
    
    return output_parsed
    

@decorator.register_test(tier=3)
def test_xpi(err, package_contents, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness"""
    
    # Skip over incompatible (or unnecessary) package types.
    if err.detected_type not in (PACKAGE_EXTENSION,
                                 PACKAGE_THEME) or \
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
    "Tests a language pack for L10n completeness"
    
    # Don't even both with the test(s) if there's no chrome.manifest.
    if "chrome.manifest" not in package_contents:
        return None

    # Retrieve the chrome.manifest if it's cached.
    if err.get_resource("chrome.manifest"): # pragma: no cover
        chrome = err.get_resource("chrome.manifest")
    else:
        chrome_data = xpi_package.read("chrome.manifest")
        chrome = ChromeManifest(chrome_data)
        err.save_resource("chrome.manifest", chrome)
    
    pack_locales = chrome.get_triples("locale")
    locales = []
    # Find all of the locales referenced in the chrome.manifest file.
    for locale in pack_locales:
        locale_jar = locale["object"].split()
        locale_name = locale_jar[0]
        location = locale_jar[-1]
        if not location.startswith("jar:"):
            continue
        location = location[4:].split("!")[0]
        locale_desc = {"path": location,
                       "name": locale_name}
        if locale_desc not in locales:
            locales.append(locale_desc)
    
    # Get the reference packages.
    references = []
    support_references = err.get_resource("supports")
    if not support_references:
        references.append("firefox")
        err.info("Supported app missing during L10n completeness.",
                 """While testing for L10n comleteness, a list of
                 supported applications for the language pack was not
                 found. This is likely because there are no listed
                 <em:targetApplication> elements in the install.rdf
                 file.""")
    else:
        for support in support_references:
            ref_pack = XPIManager("langpacks/%s.xpi" % support)
            ref_pack_data = StringIO(ref_pack.read("en-US.jar"))
            ref_xpi = XPIManager(ref_pack_data, "en-US.jar")
            ref_xpi.app_name = support
            references.append(ref_xpi)
            
    
    
    # Iterate each locale and run tests.
    for locale in locales:
        results = []
        
        package = StringIO(xpi_package.read(locale["path"]))
        locale_jar = XPIManager(package, locale["path"])
        locale_jar.locale_name = locale["name"]
        
        # Iterate each of the reference locales.
        for reference in references:
            results.extend(_compare_packages(reference, locale_jar))
        
        # Throw errors and whatnot in a seperate function.
        _aggregate_results(err, results, locale)
        
    

def _compare_packages(reference, target):
    "Compares two L10n-compatible packages to one another."
    
    ref_files = reference.get_file_data()
    tar_files = target.get_file_data()
    
    results = []
    total_entities = 0
    
    l10n_docs = ("dtd", "properties", "xhtml", "ini", "inc")
    parsable_docs = ("dtd", "properties")
    
    for name, file_data in ref_files.items():
        
        # Skip directory entries.
        if name.endswith("/"):
            continue
        
        extension = name.split(".")[-1]
        if extension not in l10n_docs:
            continue
        parsable = extension in parsable_docs
        
        if parsable:
            ref_doc = _parse_l10n_doc(name, reference.read(name))
        else:
            ref_doc = ()
        
        tar_name = name.replace("en-US", target.locale_name)
        if tar_name not in tar_files:
            results.append({"type": "missing_files",
                            "entities": len(ref_doc),
                            "filename": tar_name})
            continue
        
        if not parsable:
            continue
        
        tar_doc = _parse_l10n_doc(tar_name, target.read(tar_name))
        
        missing_entities = []
        unchanged_entities = []
        
        for rname, rvalue in ref_doc.entities.items():
            if rname not in tar_doc.entities:
                missing_entities.append(rname)
                continue
            
            if rvalue == tar_doc.entities[rname]:
                unchanged_entities.append(rname)
                continue
            
            total_entities += 1
        
        if missing_entities:
            results.append({"type": "missing_entities",
                            "entities": len(missing_entities),
                            "filename": name,
                            "missing_entities": missing_entities})
        if unchanged_entities:
            results.append({"type": "unchanged_entity",
                            "entities": len(unchanged_entities),
                            "filename": name,
                            "unchanged_entities": unchanged_entities})
    
    results.append({"type": "total_entities",
                    "entities": total_entities})
    return results
    

def _parse_l10n_doc(name, doc):
    "Parses an L10n document."
    
    wrapper = StringIO(doc)
    extension = name.split(".")[-1].lower()
    
    handlers = {"dtd":
                    testcases.l10n.dtd.DTDParser,
                "properties":
                    testcases.l10n.properties.PropertiesParser}
    if extension not in handlers:
        return None
    
    return handlers[extension](StringIO(doc))

def _aggregate_results(err, results, locale):
    """Compiles the errors and warnings in the L10n results list into
    error bundler errors and warnings."""
    
    total_entities = 0
    unchanged_entities = 0
    unchanged_entity_list = []
    
    for ritem in results:
        if "filename" in ritem:
            rfilename = ritem["filename"].replace("en-US",
                                                  locale["name"])
        
        if ritem["type"] == "missing_files":
            err.error("%s missing translation file (%s)" %
                            (locale,
                             ritem["filename"]),
                      """Localizations must include a translated copy
                      of each file in the reference locale. The
                      required files may vary from target application
                      to target application.""",
                      [locale])
        elif ritem["type"] == "missing_entities":
            err.error("%s missing %s in %s" %
                            (locale,
                             ", ".join(ritem["missing_entities"]),
                             ritem["filename"]),
                      """Localizations must include a translated copy
                      of each entity from each file in the reference
                      locale. The required files may vary from target
                      application to target application.""",
                      [locale, ritem["filename"]])
        elif ritem["type"] == "unchanged_entities":
            unchanged_entities += ritem["entities"]
            unchanged_entity_list.extend(ritem["unchanged_entities"])
        elif ritem["type"] == "total_entities":
            total_entities += ritem["entities"]
    
    total_entities += unchanged_entities
    if total_entities > 0 and \
       unchanged_entities / total_entities >= L10N_THRESHOLD:
        
        err.error("%s contains %d unchanged entities (%s)" %
                    (locale,
                     unchanged_entities,
                     ", ".join(unchanged_entity_list)),
                  """Localizations must include a translated copy
                  of each entity from each file in the reference
                  locale. These translations SHOULD differ from
                  the localized text in the reference package.""",
                  [locale, ritem["filename"]])
    

def _process_results(err, data):
    "Processes the output of the SILME script."
    
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
        

