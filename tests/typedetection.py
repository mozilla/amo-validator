from xml.dom.minidom import parse

def detect_type(install_rdf=None, xpi_package=None):
    """Determines the type of addon being validated based on
    install.rdf, file extension, and other properties."""
    
    # The types in the install.rdf don't pair up 1:1 with the type
    # system that we're using for expectations and the like. This is
    # to help translate between the two.
    translated_types = {"2": 1, 
                        "4": 2, 
                        "8": 4, 
                        "32": 1}
    
    # If we're missing our install.rdf file, we can try to make some
    # assumptions.
    if install_rdf is None:
        types = {"xpi": 3}
        
        print "There is no install.rdf, so we'll look elsewhere."
        
        # If we know what the file type might be, return it.
        if xpi_package.extension in types:
            return types[xpi_package.extension]
        # Otherwise, we're out of luck :(
        else:
            return None
    
    
    # Attempt to locate the <em:type> node in the RDF doc.
    type_uri = install_rdf.uri("type")
    type_ = install_rdf.get_object(None, type_uri)
    
    if type_ is not None:
        if type_ in translated_types:
            print "Found em:type in install.rdf"
            
            # Make sure we translate back to the normalized version
            return translated_types[type_]
            
    else:
        print "No em:type element found in install.rdf"    
    
    # Dictionaries are weird too, they might not have the obligatory
    # em:type. We can assume that if they have a /dictionaries/ folder,
    # they are a dictionary because even if they aren't, dictionaries
    # have an extraordinarily strict set of rules and file filters that
    # must be passed. It's so crazy secure that it's cool if we use it
    # as kind of a fallback.
    
    package_contents = xpi_package.get_file_data()
    dictionaries = [file_ for file_ in package_contents.keys() if
                    file_.startswith("dictionaries")]
    if dictionaries:
        print "We found indiciations of a dictionary package."
        return 3 # Dictionary
    
    
    # There's no type element, so the spec says that it's either a
    # theme or an extension. At this point, we know that it isn't
    # a dictionary, language pack, or multiple extension pack.
    
    extensions = {"jar": "4",
                  "xpi": "2"}
    
    # If the package's extension is listed in the [tiny] extension
    # dictionary, then just return that. We'll validate against that
    # addon type's layout later. Better to false positive than to false
    # negative.
    if xpi_package.extension in extensions:
        # Make sure it gets translated back to the normalized version
        install_rdf_type = extensions[xpi_package.extension]
        return translated_types[install_rdf_type]
    
    # Otherwise, the extension doesn't qualify to be validated.
    return None


def detect_opensearch(package):
    "Detect, parse, and validate an OpenSearch provider"
    
    # Parse the file.
    try:
        print "Attempting to parse..."
        srch_prov = parse(package)
    except:
        # Don't worry that it's a catch-all exception handler; it failed
        # and that's all that matters.
        return {"failure": True,
                "decided": False,
                "error": "There was an error parsing the file."}
    
    print "Testing OpenSearch for well-formedness..."
    
    # Make sure that the root element is OpenSearchDescription.
    if srch_prov.documentElement.tagName != "OpenSearchDescription":
        return {"failure": True,
                "decided": False, # Sketch, but we don't really know.
                "error": "Provider is not a valid OpenSearch provider"}
    
    # Make sure that there is exactly one ShortName.
    if not srch_prov.documentElement.getElementsByTagName("ShortName"):
        return {"failure": True,
                "error": "Missing <ShortName> element"}
    
    
    # Make sure that there is exactly one Description.
    if not srch_prov.documentElement.getElementsByTagName("Description"):
        return {"failure": True,
                "error": "Missing <Description> element"}
    
    # Grab the URLs and make sure that there is at least one.
    urls = srch_prov.documentElement.getElementsByTagName("Url")
    if not urls:
        return {"failure": True,
                "error": "Missing <Url /> elements"}
    
    acceptable_mime_types = ("text/html",
                             "application/xhtml+xml",
                             "text/xml",
                             "application/rss+xml"
                             "application/json",
                             "application/opensearchdescription+xml")
    
    # Make sure that each Url has the require attributes.
    for url in urls:
        # Test for attribute presence.
        keys = url.attributes.keys()
        if not ("type" in keys and 
                "template" in keys):
            return {"failure": True,
                    "error": "A <Url /> element is missing attributes"}
        
        # Make sure that the type attribute is an acceptable mime type.
        if not url.attributes["type"].value in acceptable_mime_types:
            # Make a nice error message about the MIME type.
            error_mesg = "The provided MIME type (%s) is not acceptable"
            error_mesg = error_mesg % url.attributes["type"].value
            return {"failure": True,
                    "error": error_mesg} 
        
        # Make sure that there is a {searchTerms} placeholder in the
        # URL template.
        found_template = \
            url.attributes["template"].value.count("{searchTerms}") < 1
        
        # If we didn't find it in a simple parse of the template=""
        # attribute, look deeper at the <Param /> elements.
        if not found_template:
            for param in url.getElementsByTagName("Param"):
                # As long as we're in here and dependent on the
                # attributes, we'd might as well validate them.
                attribute_keys = param.attributes.keys()
                if not "name" in attribute_keys or \
                   not "value" in attribute_keys:
                    return {"failure": True,
                            "error": "<Param /> missing attributes."}
                
                param_value = param.attributes["value"].value
                if param_value.count("{searchTerms}"):
                    found_template = True
                    
                    # Since we're in a validating spirit, continue
                    # looking for more errors and don't break
        
        if not found_template:
            ver = (url.attributes["template"].value,
                   url.attributes["type"].value)
            
            return {"failure": True,
                    "error": "The template for %s:%s is missing" % ver}
    
    # Make sure there are no updateURL elements
    print "Testing for banned elements..."
    if srch_prov.getElementsByTagName("updateURL"):
        return {"failure": True,
                "error": "<updateURL> elements are banned from search"}
    
    # The OpenSearch provider is valid!
    return {"failure": False,
            "error": None}
    
    