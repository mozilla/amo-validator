import actions

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
    "window": {"value": lambda: GLOBAL_ENTITIES},
    "document":
        {"value": {"createElement":
                       {"dangerous": lambda a,t: t(a[0]).get_literal_value() == "script"},
                   "createElementNS":
                       {"dangerous": lambda a,t: t(a[0]).get_literal_value() == "script"}}},
    
    # The nefariuos timeout brothers!
    "setTimeout": {"dangerous": actions._call_settimeout},
    "setInterval": {"dangerous": actions._call_settimeout},
    
    "encodeURI": {"readonly": True},
    "decodeURI": {"readonly": True},
    "encodeURIComponent": {"readonly": True},
    "decodeURIComponent": {"readonly": True},
    "escape": {"readonly": True},
    "unescape": {"readonly": True},
    "isFinite": {"readonly": True},
    "isNaN": {"readonly": True},
    "parseFloat": {"readonly": True},
    "parseInt": {"readonly": True},
    
    "eval": {"dangerous": True},
    "Function": {"dangerous": True},
    "Object": {"value": {"prototype": {"dangerous": True},
                         "constructor": # Just an experiment for now
                             {"value":lambda:GLOBAL_ENTITIES["Function"]}},},
    "String": {"value": {"prototype": {"dangerous": True}}},
    "Array": {"value": {"prototype": {"dangerous": True}}},
    "Number": {"value": {"prototype": {"dangerous": True}}},
    "Boolean": {"value": {"prototype": {"dangerous": True}}},
    "RegExp": {"value": {"prototype": {"dangerous": True}}},
    "Date": {"value": {"prototype": {"dangerous": True}}},
    
    "Math": {"readonly": True},
    
    "netscape":
        {"value": {"security":
                       {"value": {"PrivilegeManager":
                                      {"value": {"enablePrivilege":
                                                     {"dangerous": True}}}}}}},
    
    "navigator":
        {"value": {"wifi": {"dangerous": True},
                   "geolocation": {"dangerous": True}}},
    
    "Components":
        {"readonly": True,
         "value": {"utils":
                       {"value": {"evalInSandbox":
                                     {"dangerous": True},
                                  "import":
                                     {"dangerous":
                                         lambda a,t: a and a[0].contains("ctypes.jsm")}}},
                   "interfaces":
                       {"value": {"nsIProcess":
                                     {"dangerous": True},
                                  "nsIDOMGeoGeolocation":
                                     {"dangerous": True},
                                  "nsIX509CertDB":
                                     {"dangerous": True},
                                  "mozIJSSubScriptLoader":
                                     {"dangerous": True}}}}},
    "extensions": {"dangerous": True},
    "xpcnativewrappers": {"dangerous": True},
    
    # Global properties are inherently read-only, though this formalizes it.
    "Infinity": {"readonly": True},
    "NaN": {"readonly": True},
    "undefined": {"readonly": True},
    }
