import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import xpcom_constructor as xpcom_const, python_wrap
from entity_values import entity
from jstypes import JSWrapper


# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = {
    u"newThread": "Creating threads from JavaScript is a common cause "
                  "of crashes and is unsupported in recent versions of the platform",
    u"processNextEvent": "Spinning the event loop with processNextEvent is a common "
                         "cause of deadlocks, crashes, and other errors due to "
                         "unintended reentrancy. Please use asynchronous callbacks "
                         "instead wherever possible",
}

BANNED_PREF_BRANCHES = [
    u"browser.preferences.instantApply",
    u"capability.policy.",
    u"extensions.alwaysUnpack",
    u"extensions.blocklist.",
    u"extensions.bootstrappedAddons",
    u"extensions.checkCompatibility",
    u"extensions.dss.",
    u"extensions.getAddons.",
    u"extensions.getMoreThemesURL",
    u"extensions.installCache",
    u"extensions.lastAppVersion",
    u"extensions.pendingOperations",
    u"extensions.update.",
    u"general.useragent.",
    u"network.http.",
    u"network.websocket.",
    u"nglayout.debug.disable_xul_cache",
]

BANNED_PREF_REGEXPS = [
    r"extensions\..*\.update\.(url|enabled|interval)",
]


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

CONTENT_DOCUMENT = None


INTERFACES = {
    u"nsICategoryManager":
        {"value":
            {u"addCategoryEntry":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and \
                        ("Bootstrapped add-ons may not create persistent "
                         "category entries."
                         if len(a) > 3 and t(a[3]).is_literal() else
                         "Authors of bootstrapped add-ons must take care to "
                         "clean up any added category entries at shutdown.")}}},
    u"nsIAccessibleRetrieval":
        {"dangerous":
            "Using the nsIAccessibleRetrieval interface causes significant "
            "performance degradation in Gecko. It should only be used in "
            "accessibility-related add-ons."},
    u"nsIBrowserSearchService":
        {"value":
            {u"currentEngine": {"readonly": True},
             u"defaultEngine": {"readonly": True}}},

    u"nsIComm4xProfile":
        {"return": call_definitions.nsIComm4xProfile_removed},
    u"nsIComponentRegistrar":
        {"value":
            {u"autoRegister":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Bootstrapped add-ons may not register chrome "
                        "manifest files."},
             u"registerFactory":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care to "
                        "clean up any component registrations at shutdown."}}},
    u"nsIDOMNSHTMLElement": entity("nsIDOMNSHTMLElement"),
    u"nsIDOMNSHTMLFrameElement": entity("nsIDOMNSHTMLFrameElement"),
    u"nsIImapIncomingServer":
        {"value":
            {u"GetImapConnectionAndLoadUrl":
                {"return": call_definitions.TB12_nsIImapProtocol_changed}}},
    u"nsIImapMailFolderSink":
        {"value":
            {u"setUrlState":
                {"return": call_definitions.nsIImapMailFolderSink_changed}}},
    u"nsIImapProtocol":
        {"value":
            {u"NotifyHdrsToDownload":
                {"return": call_definitions.nsIImapProtocol_removed},
             u"Initialize":
                {"return": call_definitions.TB12_nsIImapProtocol_changed}}},
    u"nsIImportMail":
        {"value":
            {u"ImportMailbox": entity("nsIImportMail.ImportMailbox")}},
    u"nsIJSON":
        {"value":
            {u"encode":
                {"return": call_definitions.nsIJSON_deprec},
             u"decode":
                {"return": call_definitions.nsIJSON_deprec}}},
    u"nsIMailtoUrl":
        {"value":
            {u"GetMessageContents":
                {"return": call_definitions.nsIMailtoUrl_changed}}},
    u"nsIMsgDBService":
        {"value":
            {u"openMailDBFromFile":
                {"return": call_definitions.nsIMsgDatabase_changed}}},
    u"nsIMsgDatabase":
        {"value":
            {u"Open":
                {"return": call_definitions.nsIMsgDatabase_changed}}},
    u"nsIMsgFolder":
        {"value":
            {u"offlineStoreOutputStream":
                {"value": call_definitions.nsIMsgFolder_changed}}},
    u"nsIMsgLocalMailFolder":
        {"value":
            {u"addMessage":
                {"return": call_definitions.TB13_nsIMsgLocalMailFolder_changed},
             u"addMessageBatch":
                {"return": call_definitions.TB13_nsIMsgLocalMailFolder_changed}}},
    u"nsIMsgNewsFolder":
        {"value":
            {u"getGroupPasswordWithUI":
                {"return": call_definitions.TB13_nsIMsgNewsFolder_changed},
             u"getGroupUsernameWithUI":
                {"return": call_definitions.TB13_nsIMsgNewsFolder_changed},
             u"forgetGroupUsername":
                {"return": call_definitions.TB13_nsIMsgNewsFolder_changed},
             u"forgetGroupPassword":
                {"return": call_definitions.TB13_nsIMsgNewsFolder_changed}}},
    u"nsIMsgPluggableStore":
        {"value":
            {u"copyMessages": entity("nsIMsgPluggableStore.copyMessages")}},
    u"nsIMsgOutputStream":
        {"value":
            {u"folderStream":
                {"value": call_definitions.nsIMsgDatabase_changed}}},
    u"nsIMsgQuote":
        {"value":
            {u"quoteMessage":
                {"return": call_definitions.nsIMsgQuote_changed}}},
    u"nsIMsgSearchScopeTerm":
        {"value":
            {u"mailFile":
                {"return": call_definitions.nsIMsgSearchScopeTerm_removed},
             u"inputStream":
                {"return": call_definitions.nsIMsgSearchScopeTerm_removed}}},
    u"nsIMsgThread":
        {"value":
            {u"GetChildAt":
                {"return": call_definitions.nsIMsgThread_removed}}},
    u"nsIObserverService":
        {"value":
            {u"addObserver":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers "
                        "at shutdown."}}},
    u"nsIResProtocolHandler":
        {"value":
            {u"setSubstitution":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        a and len(a) > 1 and t(a[1]).get_literal_value() and
                        "Authors of bootstrapped add-ons must take care "
                        "to clean up any added resource substitutions "
                        "at shutdown."}}},
    u"nsIStringBundleService":
        {"value":
            {u"createStringBundle":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to flush the string bundle cache at shutdown."},
             u"createExtensibleBundle":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to flush the string bundle cache at shutdown."}}},
    u"nsIStyleSheetService":
        {"value":
            {u"loadAndRegisterSheet":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care to "
                        "unregister registered stylesheets at shutdown."}}},
    u"nsIWindowMediator":
        {"value":
            {"registerNotification":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers at shutdown."}}},
    u"nsIWindowWatcher":
        {"value":
            {u"addListener":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers at shutdown."},
             u"openWindow": entity("nsIWindowWatcher.openWindow")}},
    u"nsIURLParser":
        {"value":
             {u"parsePath":
                  {"return": call_definitions.urlparser_parsepath_bug691588}}},
    u"nsIURL":
        {"value":
             {u"param":
                  {"value": call_definitions.url_param_bug691588}}},
    u"nsIBrowserHistory":
        {"value":
             {u"lastPageVisited": entity("nsIBrowserHistory.lastPageVisited"),
              u"removePages":
                  {"return": call_definitions.browserhistory_removepages},
              u"registerOpenPage":
                  {"value": call_definitions.browserhistory_registeropenpage},
              u"unregisterOpenPage":
                  {"value":
                       call_definitions.browserhistory_unregisteropenpage},
              }
         },
    u"nsIEditorSpellCheck":
        {"value":
             {u"UpdateCurrentDictionary":
                  {"return":
                       call_definitions.spellcheck_updatecurrentdictionary},
              u"saveDefaultDictionary":
                  {"value":
                       call_definitions.spellcheck_savedefaultdictionary}}},
    u"nsIPlacesImportExportService":
        {"value":
             {u"importHTMLFromFile": entity("importHTMLFromFile"),
              u"importHTMLFromURI": entity("importHTMLFromURI"),}},
    u"nsIDOMHTMLDocument":
        {"value":
             {u"queryCommandText": entity("nsIDOMHTMLDocument"),
              u"execCommandShowHelp": entity("nsIDOMHTMLDocument")}},
    }

INTERFACE_ENTITIES = {u"nsIXMLHttpRequest":
                          {"xpcom_map":
                               lambda: GLOBAL_ENTITIES["XMLHttpRequest"]},
                      u"nsIProcess": {"dangerous": True},
                      u"nsIDOMGeoGeolocation": {"dangerous": True},
                      u"nsIX509CertDB": {"dangerous": True}}
for interface in INTERFACES:
    def construct(interface):
        def wrap():
            return INTERFACES[interface]
        return wrap
    INTERFACE_ENTITIES[interface] = {"xpcom_map": construct(interface)}


def build_quick_xpcom(method, interface, traverser):
    """A shortcut to quickly build XPCOM objects on the fly."""
    constructor = xpcom_const(method, pretraversed=True)
    interface_obj = traverser._build_global(
                        name=method,
                        entity={"xpcom_map": lambda: INTERFACES[interface]})
    obj = constructor(None, [interface_obj], traverser)
    if isinstance(obj, JSWrapper):
        obj = obj.value
    return obj


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": lambda t: {"value": GLOBAL_ENTITIES}},
    u"null": {"literal": lambda t: JSWrapper(None, traverser=t)},
    u"Cc": {"readonly": False,
            "value":
                lambda t: GLOBAL_ENTITIES["Components"]["value"]["classes"]},
    u"Ci": {"readonly": False,
            "value":
                lambda t: GLOBAL_ENTITIES["Components"]["value"]["interfaces"]},

    u"Cu": {"readonly": False,
            "value":
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
        {"value":
             {u"title":
                  {"overwriteable": True,
                   "readonly": False},
              u"defaultView":
                  {"value": lambda t: {"value": GLOBAL_ENTITIES}},
              u"createElement":
                  {"dangerous":
                       lambda a, t, e:
                           not a or _get_as_str(t(a[0])).lower() == "script"},
              u"createElementNS":
                  {"dangerous":
                       lambda a, t, e:
                           not a or _get_as_str(t(a[0])).lower() == "script"},
              u"getSelection":
                  {"return": call_definitions.document_getSelection},
              u"loadOverlay":
                  {"dangerous":
                       lambda a, t, e:
                           not a or not _get_as_str(t(a[0])).lower()
                               .startswith(("chrome:", "resource:"))},
              u"xmlEncoding": entity("document.xmlEncoding"),
              u"xmlVersion": entity("document.xmlVersion"),
              u"xmlStandalone": entity("document.xmlStandalone")}},

    # The nefariuos timeout brothers!
    u"setTimeout": {"dangerous": actions._call_settimeout},
    u"setInterval": {"dangerous": actions._call_settimeout},

    u"requestAnimationFrame": {"return":
                                   call_definitions.requestAnimationFrame},

    # mail Attachment API Functions
    u"createNewAttachmentInfo": {"return": call_definitions.mail_attachment_api},
    u"saveAttachment": {"return": call_definitions.mail_attachment_api},
    u"attachmentIsEmpty": {"return": call_definitions.mail_attachment_api},
    u"openAttachment": {"return": call_definitions.mail_attachment_api},
    u"detachAttachment": {"return": call_definitions.mail_attachment_api},
    u"cloneAttachment": {"return": call_definitions.mail_attachment_api},
    u"FocusOnFirstAttachment": {"return": call_definitions.TB9FocusFunctions_removed},

    u"gComposeBundle": {"return": call_definitions.gComposeBundle_removed},
    u"WhichPaneHasFocus": {"return": call_definitions.TB9FocusFunctions_removed},

    # Thunderbird 10 global functions changed/removed
    u"MsgDeleteMessageFromMessageWindow": {"return": call_definitions.TB10Function_removed},
    u"goToggleSplitter": {"return": call_definitions.TB10Function_removed},
    u"AddMessageComposeOfflineObserver": {"return": call_definitions.TB10Function_renamed},
    u"RemoveMessageComposeOfflineObserver": {"return": call_definitions.TB10Function_renamed},

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
    u"Object":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":  # Just an experiment for now
                  {"value": lambda t: GLOBAL_ENTITIES["Function"]}}},
    u"String":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.string_global},
    u"Array":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.array_global},
    u"Number":
        {"value":
             {u"prototype":
                  {"readonly": True},
              u"POSITIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('inf'), traverser=t)},
              u"NEGATIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('-inf'), traverser=t)}},
         "return": call_definitions.number_global},
    u"Boolean":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.boolean_global},
    u"RegExp": {"value": {u"prototype": {"readonly": True}}},
    u"Date": {"value": {u"prototype": {"readonly": True}}},
    u"File": {"value": {u"prototype": {"readonly": True}}},

    u"Math":
        {"value":
             {u"PI":
                  {"value": lambda t: JSWrapper(math.pi, traverser=t)},
              u"E":
                  {"value": lambda t: JSWrapper(math.e, traverser=t)},
              u"LN2":
                  {"value": lambda t: JSWrapper(math.log(2), traverser=t)},
              u"LN10":
                  {"value": lambda t: JSWrapper(math.log(10), traverser=t)},
              u"LOG2E":
                  {"value": lambda t: JSWrapper(math.log(math.e, 2),
                                                traverser=t)},
              u"LOG10E":
                  {"value": lambda t: JSWrapper(math.log10(math.e),
                                                traverser=t)},
              u"SQRT2":
                  {"value": lambda t: JSWrapper(math.sqrt(2), traverser=t)},
              u"SQRT1_2":
                  {"value": lambda t: JSWrapper(math.sqrt(1/2), traverser=t)},
              u"abs":
                  {"return": python_wrap(abs, [("num", 0)])},
              u"acos":
                  {"return": python_wrap(math.acos, [("num", 0)])},
              u"asin":
                  {"return": python_wrap(math.asin, [("num", 0)])},
              u"atan":
                  {"return": python_wrap(math.atan, [("num", 0)])},
              u"atan2":
                  {"return": python_wrap(math.atan2, [("num", 0),
                                                      ("num", 1)])},
              u"ceil":
                  {"return": python_wrap(math.ceil, [("num", 0)])},
              u"cos":
                  {"return": python_wrap(math.cos, [("num", 0)])},
              u"exp":
                  {"return": python_wrap(math.exp, [("num", 0)])},
              u"floor":
                  {"return": python_wrap(math.floor, [("num", 0)])},
              u"log":
                  {"return": call_definitions.math_log},
              u"max":
                  {"return": python_wrap(max, [("num", 0)], nargs=True)},
              u"min":
                  {"return": python_wrap(min, [("num", 0)], nargs=True)},
              u"pow":
                  {"return": python_wrap(math.pow, [("num", 0),
                                                    ("num", 0)])},
              u"random": # Random always returns 0.5 in our fantasy land.
                  {"return": call_definitions.math_random},
              u"round":
                  {"return": call_definitions.math_round},
              u"sin":
                  {"return": python_wrap(math.sin, [("num", 0)])},
              u"sqrt":
                  {"return": python_wrap(math.sqrt, [("num", 1)])},
              u"tan":
                  {"return": python_wrap(math.tan, [("num", 0)])},
                  }},

    u"netscape":
        {"value":
             {u"security":
                  {"value":
                       {u"PrivilegeManager":
                            {"value":
                                 {u"enablePrivilege":
                                      {"dangerous": True}}}}}}},
    u"navigator":
        {"value": {u"wifi": {"dangerous": True},
                   u"geolocation": {"dangerous": True}}},

    u"Components":
        {"dangerous_on_read":
             lambda t, e: bool(e.metadata.get("is_jetpack")),
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
                                          a and "ctypes.jsm" in _get_as_str(t(a[0]))}}},
              u"interfaces": {"value": INTERFACE_ENTITIES}}},
    u"extensions": {"dangerous": True},
    u"xpcnativewrappers": {"dangerous": True},

    u"AddonManagerPrivate":
        {"value":
            {u"registerProvider": {"return": call_definitions.amp_rp_bug660359}}},

    u"XMLHttpRequest":
        {"value":
             {u"open":
                  {"dangerous":
                       # Ban synchronous XHR by making sure the third arg
                       # is absent and false.
                       lambda a, t, e:
                           a and len(a) >= 3 and
                           not t(a[2]).get_literal_value() and
                           "Synchronous HTTP requests can cause serious UI "
                           "performance problems, especially to users with "
                           "slow network connections."}}},

    # Global properties are inherently read-only, though this formalizes it.
    u"Infinity":
        {"value":
             lambda t:
                 GLOBAL_ENTITIES[u"Number"]["value"][u"POSITIVE_INFINITY"]},
    u"NaN": {"readonly": True},
    u"undefined": {"readonly": True},

    u"innerHeight": {"readonly": False},
    u"innerWidth": {"readonly": False},
    u"width": {"readonly": False},
    u"height": {"readonly": False},
    u"top": {"readonly": actions._readonly_top},

    u"content":
        {"context": "content",
         "value":
             {u"document":
                  {"value": lambda t: GLOBAL_ENTITIES[u"document"]}}},
    u"contentWindow":
        {"context": "content",
         "value":
             lambda t: {"value": GLOBAL_ENTITIES}},
    u"_content": {"value": lambda t: GLOBAL_ENTITIES[u"content"]},
    u"gBrowser":
        {"value":
             {u"contentDocument":
                  {"context": "content",
                   "value": lambda t: CONTENT_DOCUMENT},
              u"contentWindow":
                  {"value":
                       lambda t: {"value": GLOBAL_ENTITIES}},
              u"selectedTab":
                  {"readonly": False}}},
    u"opener":
        {"value":
             lambda t: {"value": GLOBAL_ENTITIES}},

    u"XPCNativeWrapper":
        {"value":
             {u"unwrap":
                  {"return": call_definitions.js_unwrap}},
         "return": call_definitions.js_wrap},

    # Preference creation in pref defaults files
    u"pref": {"dangerous": actions._call_create_pref},
    u"user_pref": {"dangerous": actions._call_create_pref},

    u"unsafeWindow": {"dangerous": "The use of unsafeWindow is insecure and "
                                   "should be avoided whenever possible. "
                                   "Consider using a different API if it is "
                                   "available in order to achieve similar "
                                   "functionality."},
}

CONTENT_DOCUMENT = GLOBAL_ENTITIES[u"content"]["value"][u"document"]
