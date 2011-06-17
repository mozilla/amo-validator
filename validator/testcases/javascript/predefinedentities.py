import actions
import call_definitions
from call_definitions import xpcom_constructor as xpcom_const
from jstypes import JSWrapper

# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = ("newThread", )

# For "dangerous" elements, specifying True will throw an error on all
# detected instances of the particular object. Specifying a lambda function
# will allow the object to be referenced. If the object is called via a
# CallExpression, "a" will contain the raw arguments values and "t" will
# contain a reference to traverser._traverse_node(). "t" will always return a
# JSWrapper object. The optional third argument "e" will be an ErrorBundle
# object. The return value of the lambda function will be used as the value for
# the "dangerous" property. Lastly, specifying a string functions identically to
# "True", except the string will be outputted when the error is thrown.

INTERFACES = {
    u"nsICategoryManager":
        {"value":
            {u"addCategoryEntry":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        ("Bootstrapped add-ons may not create persistent "
                         "category entries"
                         if a and len(a) > 3 and t(a[3]).get_literal_value()
                         else
                         "Authors of bootstrapped add-ons must take care "
                         "to cleanup any added category entries "
                         "at shutdown")}}},
    u"nsIComponentRegistrar":
        {"value":
            {u"autoRegister":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Bootstrapped add-ons may not register "
                        "chrome manifest files"},
             u"registerFactory":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to cleanup any component registrations "
                        "at shutdown"}}},
    u"nsIObserverService":
        {"value":
            {u"addObserver":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers "
                        "at shutdown"}}},
    u"nsIResProtocolHandler":
        {"value":
            {u"setSubstitution":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        a and \
                        len(a) > 1 and  \
                        t(a[1]).get_literal_value() and \
                        "Authors of bootstrapped add-ons must take care "
                        "to cleanup any added resource substitutions "
                        "at shutdown"}}},
    u"nsIStringBundleService":
        {"value":
            {u"createStringBundle":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to flush the string bundle cache at shutdown"},
             u"createExtensibleBundle":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to flush the string bundle cache at shutdown"}}},
    u"nsIStyleSheetService":
        {"value":
            {u"loadAndRegisterSheet":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to unregister any registered stylesheets "
                        "at shutdown"}}},
    u"nsIWindowMediator":
        {"value":
            {"registerNotification":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers "
                        "at shutdown"}}},
    u"nsIWindowWatcher":
        {"value":
            {u"addListener":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers "
                        "at shutdown"}}},
    }


def build_quick_xpcom(method, interface, traverser):
    """A shortcut to quickly build XPCOM objects on the fly."""
    constructor = xpcom_const(method, pretraversed=True)
    interface_obj = traverser._build_global(
                        name=method,
                        entity={"xpcom_map": lambda: INTERFACES[interface]})
    object = constructor(None, [interface_obj], traverser)
    if isinstance(object, JSWrapper):
        object = object.value
    return object


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": lambda t: {"value": GLOBAL_ENTITIES}},
    u"Cc": {"value":
                lambda t: GLOBAL_ENTITIES["Components"]["value"]["classes"]},
    u"Ci": {"value":
                lambda t: GLOBAL_ENTITIES["Components"]["value"]["interfaces"]},

    u"Cu": {"value":
                lambda t: GLOBAL_ENTITIES["Components"]["value"]["utils"]},
    u"Services":
        {"value": {u"scriptloader": {"dangerous": True},
                   u"wm":
                       {"value":
                            lambda t: build_quick_xpcom("getService",
                                                        "nsIWindowMediator",
                                                        t)},
                   u"ww":
                       {"value":
                            lambda t: build_quick_xpcom("getService",
                                                        "nsIWindowWatcher",
                                                        t)}}},

    u"document":
        {"value": {u"title":
                       {"overwriteable": True,
                        "readonly": False},
                   u"createElement":
                       {"dangerous":
                            lambda a, t, e: not a or
                                            unicode(t(a[0]).get_literal_value())
                                                .lower() == "script"},
                   u"createElementNS":
                       {"dangerous":
                            lambda a, t, e: not a or
                                            unicode(t(a[0]).get_literal_value())
                                                .lower() == "script"},
                   u"loadOverlay":
                       {"dangerous":
                            lambda a, t, e:
                                not a or
                                not unicode(t(a[0]).get_literal_value())
                                        .lower()
                                        .startswith(("chrome:",
                                                     "resource:"))}}},

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
    u"Object": {"value": {u"prototype": {"readonly": True},
                          u"constructor":  # Just an experiment for now
                              {"value": lambda t: GLOBAL_ENTITIES["Function"]}}},
    u"String": {"value": {u"prototype": {"readonly": True}}},
    u"Array": {"value": {u"prototype": {"readonly": True}}},
    u"Number": {"value": {u"prototype": {"readonly": True}}},
    u"Boolean": {"value": {u"prototype": {"readonly": True}}},
    u"RegExp": {"value": {u"prototype": {"readonly": True}}},
    u"Date": {"value": {u"prototype": {"readonly": True}}},

    u"top": {"readonly": actions._readonly_top},

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
                  {"xpcom_wildcard": True,
                   "value":
                       {u"createInstance":
                           {"return": xpcom_const("createInstance")},
                        u"getService":
                           {"return": xpcom_const("getService")}}},
              "utils":
                  {"value": {u"evalInSandbox":
                                 {"dangerous": True},
                             u"import":
                                 {"dangerous":
                                      lambda a, t, e:
                                        a and \
                                        unicode(t(a[0]).get_literal_value())
                                            .count("ctypes.jsm")}}},
              u"interfaces":
                  {"value": {u"nsIXMLHttpRequest":
                                {"xpcom_map":
                                     lambda:
                                        GLOBAL_ENTITIES["XMLHttpRequest"]},
                             u"nsICategoryManager":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsICategoryManager"]},
                             u"nsIComponentRegistrar":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIComponentRegistrar"]},
                             u"nsIObserverService":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIObserverService"]},
                             u"nsIResProtocolHandler":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIResProtocolHandler"]},
                             u"nsIStyleSheetService":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIStyleSheetService"]},
                             u"nsIStringBundleService":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIStringBundleService"]},
                             u"nsIWindowMediator":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIWindowMediator"]},
                             u"nsIWindowWatcher":
                                {"xpcom_map":
                                     lambda:
                                        INTERFACES["nsIWindowWatcher"]},
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

    u"AddonManagerPrivate":
        {"value":
            {u"registerProvider": {"return": call_definitions.amp_rp_bug660359}}},

    u"XMLHttpRequest":
        {"value":
             {u"open": {"dangerous":
                           # Ban syncrhonous XHR by making sure the third arg
                           # is not absent and falsey.
                           lambda a, t, e:
                               a and len(a) >= 3 and
                               not t(a[2]).get_literal_value() and
                               "Synchronous HTTP requests can cause "
                               "serious UI performance problems, "
                               "especially to users with slow network "
                               "connections."}}},

    # Global properties are inherently read-only, though this formalizes it.
    u"Infinity": {"readonly": True},
    u"NaN": {"readonly": True},
    u"undefined": {"readonly": True},

    u"innerHeight": {"readonly": False},
    u"innerWidth": {"readonly": False},
    u"width": {"readonly": False},
    u"height": {"readonly": False},
    }
