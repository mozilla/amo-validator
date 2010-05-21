from xml.dom.minidom import parse

import rdflib
from rdflib import URIRef

import xpi
import rdf


def detect_type(install_rdf=None, xpi_package=None):
    """Determines the type of addon being validated based on
    install.rdf, file extension, and other properties."""
    
    # The types in the install.rdf don't pair up 1:1 with the type
    # system that we're using for expectations and the like. This is
    # to help translate between the two.
    translated_types = {"2": 1, 
                        "4": 2, 
                        "8": 4, 
                        "32": 1, 
                        }
    
    # If we're missing our install.rdf file, we can try to make some
    # assumptions.
    if install_rdf is None:
        types
        
    
    # Grab a local reference to the RDF document
    rdfDoc = install_rdf.rdf
    
    # Attempt to locate the <em:type> node in the RDF doc.
    type_uri = URIRef('http://www.mozilla.org/2004/em-rdf#type')
    type_values = rdfDoc.objects(None, type_uri)
    
	
	
    if type_values:
        # We've found at least one <em:type>. Only accept one.
        type = ""
        for t in type_values:
            type = t
        
        # We can break out and assume that the type is truthful if it
        # is a valid type value. Otherwise, ignore the type element.
        if type in translated_types:
            # Make sure we translate back to the normalized version
            return translated_types[type] 
    
    
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
    
    # Dictionaries are weird too, they might not have the obligatory
    # em:type. We can assume that if they have a /dictionaries/ folder,
    # they are a dictionary because even if they aren't, dictionaries
    # have an extraordinarily strict set of rules and file filters that
    # must be passed. It's so crazy secure that it's cool if we use it
    # as kind of a fallback.
    
    package_contents = xpi_package.get_file_data()
    if "dictionaries" in package_contents:
		return 5 # Dictionary
    
    # Otherwise, the extension doesn't qualify to be validated.
    return None


def detect_opensearch(package):
    "Detect, parse, and validate an OpenSearch provider"
    
    # Parse the file.
    try:
        print "Attempting to parse..."
        x = parse(package)
    except:
        # Don't worry that it's a catch-all exception handler; it failed
        # and that's all that matters.
        return {"failure": True,
                "error": "There was an error parsing the file."}
    
    print "Testing OpenSearch for well-formedness..."
    
    # Make sure that the root element is OpenSearchDescription.
    if x.documentElement.tagName != "OpenSearchDescription":
        return {"failure": True,
                "error": "Provider is not a valid OpenSearch provider"}
    
    # Make sure that there is exactly one ShortName.
    if not x.documentElement.getElementsByTagName("ShortName"):
        return {"failure": True,
                "error": "Missing <ShortName> element"}
    
    
    # Make sure that there is exactly one Description.
    if not x.documentElement.getElementsByTagName("Description"):
        return {"failure": True,
                "error": "Missing <Description> element"}
    
    # Grab the URLs and make sure that there is at least one.
    urls = x.documentElement.getElementsByTagName("Url")
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
        if not ("type" in keys or \
                "template" in keys):
            return {"failure": True,
                    "error": "A <Url /> element is missing attributes"}
        
        # Make sure that the type attribute is an acceptable mime type.
        if not (url.attributes["type"].value in acceptable_mime_types):
            # Make a nice error message about the MIME type.
            error_mesg = "The provided MIME type (%s) is not acceptable"
            error_mesg = error_mesg % url.attributes["type"].value
            return {"failure": True,     
                    "error": error_mesg} 
        
        # Make sure that there is a {searchTerms} placeholder in the
        # URL template.
        if url.attributes["template"].value.count("{searchTerms}") < 1:
            # Find an attribute that we can use for the name. If there
            # isn't one, then just use "noname"
            name_att = ("rel" in keys and url.attributes["rel"]) or \
                       ("type" in keys and url.attributes["type"])
            if name_att:
                name = name_att.value
            else:
                name = "(untitled)"
            return {"failure": False,
                    "error": "The template for %s is missing" % name}
        
    # The OpenSearch provider is valid!
    return {"failure": False,
            "error": None}
    
    