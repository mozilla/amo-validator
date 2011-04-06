import actions
import call_definitions

# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = ("newThread", )

# For "dangerous" elements, specifying True will throw an error on all
# detected instances of the particular object. Specifying a lambda function
# will allow the object to be referenced. If the object is called via a
# CallExpression, "a" will contain the raw arguments values and "t" will
# contain a reference to traverser._traverse_node(). "t" will always return a
# JSWrapper object. The return value of the lambda function will be used as
# the value for the "dangerous" property. Lastly, specifying a string functions
# identically to "True", except the string will be outputted when the error is
# thrown.

# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": lambda: GLOBAL_ENTITIES},
    u"document":
        {"value": {u"createElement":
                       {"dangerous":
                            lambda a, t: t(a[0]).get_literal_value()
                                                .lower() == "script"},
                   u"createElementNS":
                       {"dangerous":
                            lambda a, t: t(a[0]).get_literal_value()
                                                .lower() == "script"}}},

    # The nefariuos timeout brothers!
    u"setTimeout": {"dangerous": actions._call_settimeout},
    u"setInterval": {"dangerous": actions._call_settimeout},

    u"encodeURI": {"readonly": True},
    u"decodeURI": {"readonly": True},
    u"encodeURIComponent": {"readonly": True},
    u"decodeURIComponent": {"readonly": True},
    u"escape": {"readonly": True},
    u"unescape": {"readonly": True},
    u"isFinite": {"readonly": True},
    u"isNaN": {"readonly": True},
    u"parseFloat": {"readonly": True},
    u"parseInt": {"readonly": True},

    u"eval": {"dangerous": True},
    u"Function": {"dangerous": True},
    u"Object": {"value": {"prototype": {"dangerous": True},
                          "constructor":  # Just an experiment for now
                              {"value": lambda: GLOBAL_ENTITIES["Function"]}}},
    u"String": {"value": {"prototype": {"dangerous": True}}},
    u"Array": {"value": {"prototype": {"dangerous": True}}},
    u"Number": {"value": {"prototype": {"dangerous": True}}},
    u"Boolean": {"value": {"prototype": {"dangerous": True}}},
    u"RegExp": {"value": {"prototype": {"dangerous": True}}},
    u"Date": {"value": {"prototype": {"dangerous": True}}},

    u"Math": {"readonly": True},

    u"netscape":
        {"value": {u"security":
                       {"value": {u"PrivilegeManager":
                                      {"value": {u"enablePrivilege":
                                                     {"dangerous": True}}}}}}},

    u"navigator":
        {"value": {u"wifi": {"dangerous": True},
                   u"geolocation": {"dangerous": True}}},

    u"Components":
        {"readonly": True,
         "value":
             {u"classes":
                  {u"xpcom_wildcard": True,
                   "value":
                       {u"createInstance":
                           {"return": call_definitions.xpcom_createInstance}}},
              u"utils":
                  {"value": {u"evalInSandbox":
                                 {"dangerous": True},
                             u"import":
                                 {"dangerous":
                                      lambda a, t:
                                        a and \
                                        unicode(t(a[0]).get_literal_value())
                                            .count("ctypes.jsm")}}},
              u"interfaces":
                  {"value": {u"nsIXMLHttpRequest":
                                {"xpcom_map":
                                     lambda:
                                        GLOBAL_ENTITIES["XMLHttpRequest"]},
                             u"nsIProcess":
                                {"dangerous": True},
                             u"nsIDOMGeoGeolocation":
                                {"dangerous": True},
                             u"nsIX509CertDB":
                                {"dangerous": True},
                             u"mozIJSSubScriptLoader":
                                {"dangerous": True}}}}},
    u"extensions": {"dangerous": True},
    u"xpcnativewrappers": {"dangerous": True},

    u"XMLHttpRequest":
        {"value":
             {u"open": {"dangerous":
                           # Ban syncrhonous XHR by making sure the third arg
                           # is absent and false.
                           lambda a, t:
                               a and \
                               len(a) > 2 and \
                               not t(a[2]).get_literal_value() and \
                               "Synchronous HTTP requests can cause "
                               "serious UI performance problems, "
                               "especially to users with slow network "
                               "connections."}}},

    # Global properties are inherently read-only, though this formalizes it.
    u"Infinity": {"readonly": True},
    u"NaN": {"readonly": True},
    u"undefined": {"readonly": True},
    }
