import actions
#from traverser import JSObject, JSVariable

# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    "window": {"value": lambda: GLOBAL_ENTITIES},
    "document":
        {"value": {"createElement":
                       {"dangerous": lambda *args: args[0].value == "script"},
                   "createElementNS":
                       {"dangerous": lambda *args: args[0].value == "script"}}},
    
    # The nefariuos timeout brothers!
    "setTimeout": {"dangerous": actions._call_settimeout},
    "setInterval": {"dangerous": actions._call_settimeout},
    
    "eval": {"dangerous": True},
    "Function": {"dangerous": True},
    "Object": {"value": {"prototype": {"dangerous": True}}},
    "String": {"value": {"prototype": {"dangerous": True}}},
    "Array": {"value": {"prototype": {"dangerous": True}}},
    "Number": {"value": {"prototype": {"dangerous": True}}},
    "Boolean": {"value": {"prototype": {"dangerous": True}}},
    "Date": {"value": {"prototype": {"dangerous": True}}},
    
    "netscape":
        {"value": {"security":
                       {"value": {"PrivilegeManager":
                                      {"value": {"enablePrivilege":
                                                     {"dangerous": True}}}}}}},
    
    "navigator":
        {"value": {"wifi": {"dangerous": True},
                   "geolocation": {"dangerous": True}}},
    
    "Components":
        {"value": {"utils":
                       {"value": {"evalInSandbox":
                                     {"dangerous": True},
                                  "import":
                                     {"dangerous":
                                         lambda *args: args and args[0].contains("ctypes.jsm")}}},
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
    "xpcnativewrappers": {"dangerous": True}
    }
