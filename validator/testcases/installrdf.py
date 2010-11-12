import re

from validator import decorator
from validator.constants import *

@decorator.register_test(tier=1)
def test_install_rdf_params(err, package_contents=None, xpi_package=None):
    """Tests to make sure that some of the values in install.rdf
    are not gummed up."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    # This returns for testing reasons
    return _test_rdf(err, install)



def _test_rdf(err, install):
    """Wrapper for install.rdf testing to make unit testing so much
    easier."""
    
    if not err.get_resource("listed"):
        shouldnt_exist = ("hidden", )
    else:
        shouldnt_exist = ("updateURL",
                          "updateKey",
                          "updateLink",
                          "hidden")
    obsolete = ("file", )
    must_exist_once = ["id",
                       "version",
                       "name",
                       "targetApplication"]
    may_exist_once = ["about", # For <Description> element
                      "type",
                      "optionsURL",
                      "aboutURL",
                      "iconURL",
                      "homepageURL",
                      "creator",
                      "updateInfoURL",
                      "updateKey",
                      "updateURL",
                      "updateLink", # Banned, but if not, pass it once.
                      "updateHash",
                      "signature",
                      "unpack"] # This has other rules; CAUTION!
    may_exist = ("targetApplication",
                 "localized",
                 "description",
                 "creator",
                 "translator",
                 "contributor",
                 "targetPlatform",
                 "requires",
                 "developer")
    
    if err.detected_type == PACKAGE_THEME:
        may_exist_once.append("internalName")
    
    top_id = install.get_root_subject()
    
    for pred_raw in install.rdf.predicates(top_id, None):
        predicate = pred_raw.split("#")[-1]
        
        # Mark that the unpack element has been supplied
        if predicate == "unpack":
            value = install.get_object(predicate=pred_raw)
            err.save_resource("em:unpack", value)

        # Test if the predicate is banned
        if predicate in shouldnt_exist:
            err.error(("testcases_installrdf",
                       "_test_rdf",
                       "shouldnt_exist"),
                      "Banned element in install.rdf",
                      """The element "%s" was found in the add-on's
                      install.rdf file. It is not allowed in add-ons under
                      the current configuration.""" % predicate,
                      "install.rdf")
            continue
        
        # Test if the predicate is obsolete
        if predicate in obsolete:
            err.info(("testcases_installrdf",
                      "_test_rdf",
                      "obsolete"),
                     "Obsolete element in install.rdf",
                     """The element "%s" was found in the add-on's install.rdf
                     file. It has not been banned, but it is no longer
                     supported by any modern Mozilla product. Removing the
                     element is recommended and will not break support.""" %
                        predicate,
                     "install.rdf")
            continue
        
        # Remove the predicate from must_exist_once if it's there.
        if predicate in must_exist_once:
            
            object_value = install.get_object(None, pred_raw)
            
            # Test the predicate for specific values.
            if predicate == "id":
                _test_id(err, object_value)
            elif predicate == "version":
                _test_version(err, object_value)
            elif predicate == "name":
                _test_name(err, object_value)
            
            must_exist_once.remove(predicate)
            continue
        
        # Do the same for may_exist_once.
        if predicate in may_exist_once:
            may_exist_once.remove(predicate)
            continue
        
        # If the element is safe for repetition, continue
        if predicate in may_exist:
            continue
        
        # If the predicate isn't in any of the above lists, it is
        # invalid and needs to go.
        err.error(("testcases_installrdf",
                   "_test_rdf",
                   "unrecognized"),
                  "Unrecognized element in install.rdf",
                  """The element "%s" was found is not a part of the
                  install manifest specification, has been used too
                  many times, or is not applicable to the current
                  configuration.""" % predicate,
                  "install.rdf")
        
    # Once all of the predicates have been tested, make sure there are
    # no mandatory elements that haven't been found.
    if must_exist_once:
        missing_preds = ', '.join(must_exist_once)
        err.error(("testcases_installrdf",
                   "_test_rdf",
                   "missing_addon"),
                  "install.rdf missing element(s).",
                  ["""The element listed is a required element in the install
                   manifest specification. It must be added to your addon.""",
                   "Missing elements:",
                   missing_preds]
                  ,
                  "install.rdf")
    

def _test_id(err, value):
    "Tests an install.rdf UUID value"
    
    id_pattern = re.compile("(\{[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}\}|[a-z0-9-\.\+_]*\@[a-z0-9-\._]+)", re.I)
    
    err.metadata["id"] = value
    
    # Must be a valid UUID string.
    if not id_pattern.match(value):
        err.error(("testcases_installrdf",
                   "_test_id",
                   "invalid"),
                  "The value of <em:id> is invalid.",
                  """The values supplied for <em:id> in the
                  install.rdf file is not a valid UUID string.""",
                  "install.rdf")
    

def _test_version(err, value):
    "Tests an install.rdf version number"
    
    whitespace_pattern = re.compile("\s")
    version_pattern = re.compile("\d+(\+|\w+)?(\.\d+(\+|\w+)?)*")
    
    err.metadata["version"] = value
    
    # Cannot have whitespace in the pattern.
    if whitespace_pattern.search(value):
        err.error(("testcases_installrdf",
                   "_test_version",
                   "invalid_whitespace"),
                  "<em:version> value cannot contain whitespace.",
                  """In your addon's install.rdf file, version numbers
                  cannot contain whitespace characters of any kind.""",
                  "install.rdf")
    
    # Must be a valid version number.
    if not version_pattern.match(value):
        err.error(("testcases_installrdf",
                   "_test_version",
                   "invalid_format"),
                  "The value of <em:version> is invalid.",
                  """The values supplied for <em:version> in the
                  install.rdf file is not a valid version string.""",
                  "install.rdf")
    

def _test_name(err, value):
    "Tests an install.rdf name value for trademarks."
    
    ff_pattern = re.compile("(mozilla|firefox)", re.I)
    
    err.metadata["name"] = value
    
    if ff_pattern.match(value):
        err.error(("testcases_installrdf",
                   "_test_name",
                   "trademark"),
                  "Add-on has illegal name.",
                  """Add-on names cannot contain the Mozilla or Firefox
                  trademarks. These names should not be contained in
                  add-on names at all.""",
                  "install.rdf")

