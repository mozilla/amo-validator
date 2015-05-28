from functools import partial
import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import xpcom_constructor as xpcom_const, python_wrap
from entity_values import entity
import instanceactions
from jstypes import JSWrapper


# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = {
    u"newThread":
        "Creating threads from JavaScript is a common cause "
        "of crashes and is unsupported in recent versions of the platform",
    u"processNextEvent":
        "Spinning the event loop with processNextEvent is a common cause of "
        "deadlocks, crashes, and other errors due to unintended reentrancy. "
        "Please use asynchronous callbacks instead wherever possible",
}

CUSTOMIZATION_PREF_MESSAGE = {
    "description": (
        "Extensions must not alter user preferences such as the current home "
        "page, new tab page, or search engine, without explicit user consent, "
        "in which a user takes a non-default action. Such changes must also "
        "be reverted when the extension is disabled or uninstalled.",
        "In nearly all cases, new values for these preferences should be "
        "set in the default preference branch, rather than the user branch."),
    "signing_severity": "high",
}

NETWORK_PREF_MESSAGE = {
    "description":
        "Changing network preferences may be dangerous, and often leads to "
        "performance costs.",
    "signing_severity": "low",
}

SEARCH_PREF_MESSAGE = {
    "description":
        "Search engine preferences may not be changed by add-ons directly. "
        "All such changes must be made only via the browser search service, "
        "and only after an explicit opt-in from the user. All such changes "
        "must be reverted when the extension is disabled or uninstalled.",
    "signing_severity": "high",
}

SECURITY_PREF_MESSAGE = {
    "description":
        "Changing this preference may have severe security implications, and "
        "is forbidden under most circumstances.",
    "editors_only": True,
    "signing_severity": "high",
}

BANNED_PREF_BRANCHES = (
    # Security and update preferences
    (u"app.update.", SECURITY_PREF_MESSAGE),
    (u"browser.addon-watch.", SECURITY_PREF_MESSAGE),
    (u"capability.policy.", None),
    (u"datareporting.", SECURITY_PREF_MESSAGE),

    (u"extensions.blocklist.", SECURITY_PREF_MESSAGE),
    (u"extensions.checkCompatibility", None),
    (u"extensions.getAddons.", SECURITY_PREF_MESSAGE),
    (u"extensions.update.", SECURITY_PREF_MESSAGE),

    # Let's see if we can get away with this...
    # Changing any preference in this branch should result in a
    # warning. However, this substring may turn out to be too
    # generic, and lead to spurious warnings, in which case we'll
    # have to single out sub-branches.
    (u"security.", SECURITY_PREF_MESSAGE),

    # Search, homepage, and ustomization preferences
    (u"browser.newtab.url", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.newtabpage.enabled", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.search.defaultenginename", SEARCH_PREF_MESSAGE),
    (u"browser.search.searchEnginesURL", SEARCH_PREF_MESSAGE),
    (u"browser.startup.homepage", CUSTOMIZATION_PREF_MESSAGE),
    (u"extensions.getMoreThemesURL", None),
    (u"keyword.URL", SEARCH_PREF_MESSAGE),
    (u"keyword.enabled", SEARCH_PREF_MESSAGE),

    # Network
    (u"network.proxy.autoconfig_url", {
        "description":
            "As many add-ons have reason to change the proxy autoconfig URL, "
            "and only one at a time may do so without conflict, extensions "
            "must make proxy changes using other mechanisms. Installing a "
            "proxy filter is the recommended alternative: "
            "https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XPCOM/"
            "Reference/Interface/nsIProtocolProxyService#registerFilter()",
        "signing_severity": "low"}),
    (u"network.proxy.", NETWORK_PREF_MESSAGE),
    (u"network.http.", NETWORK_PREF_MESSAGE),
    (u"network.websocket.", NETWORK_PREF_MESSAGE),

    # Other
    (u"browser.preferences.instantApply", None),

    (u"extensions.alwaysUnpack", None),
    (u"extensions.bootstrappedAddons", None),
    (u"extensions.dss.", None),
    (u"extensions.installCache", None),
    (u"extensions.lastAppVersion", None),
    (u"extensions.pendingOperations", None),

    (u"general.useragent.", None),

    (u"nglayout.debug.disable_xul_cache", None),
)

BANNED_PREF_REGEXPS = [
    r"extensions\..*\.update\.(url|enabled|interval)",
]


def is_shared_scope(traverser, right=None, node_right=None):
    """Returns true if the traverser `t` is traversing code loaded into
    a shared scope, such as a browser window. Particularly used for
    detecting when global overwrite warnings should be issued."""

    # FIXME(Kris): This is not a great heuristic.
    return not (traverser.is_jsm or
                traverser.err.get_resource("em:bootstrap") == "true")


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

CONTENT_DOCUMENT = None


CATEGORY_MANAGER = {
    u"addCategoryEntry":
        {"dangerous":
            lambda a, t, e:
                e.get_resource("em:bootstrap") and
                ("Bootstrapped add-ons may not create persistent category "
                 "entries." if len(a) > 3 and t(a[3]).is_literal() else
                 "Authors of bootstrapped add-ons must take care to clean up "
                 "any added category entries at shutdown.")}}


OBSOLETE_EXTENSION_MANAGER = {
    "value": {},
    "dangerous": "This interface is part of the obsolete extension manager "
                 "interface, which is not available in any remotely modern "
                 "version of Firefox. It should not be referenced in any "
                 "code."}


ADDON_INSTALL_METHOD = {
    "value": {},
    "dangerous": {
        "description": (
            "Add-ons may install other add-ons only by user consent. Any "
            "such installations must be carefully reviewed to ensure "
            "their safety."),
        "editors_only": True,
        "signing_severity": "high"},
}


SEARCH_MESSAGE = "Potentially dangerous use of the search service"
SEARCH_DESCRIPTION = (
    "Changes to the default and currently-selected search engine settings "
    "may only take place after users have explicitly opted-in, by taking "
    "a non-default action. Any such changes must be reverted when the add-on "
    "making them is disabled or uninstalled.")

def search_warning(severity="medium", editors_only=False,
                   message=SEARCH_MESSAGE,
                   description=SEARCH_DESCRIPTION):
    return {"err_id": ("testcases_javascript_actions",
                       "search_service",
                       "changes"),
            "signing_severity": severity,
            "editors_only": editors_only,
            "warning": message,
            "description": description}


REGISTRY_WRITE = {"dangerous": {
    "err_id": ("testcases_javascript_actions",
               "windows_registry",
               "write"),
    "warning": "Writes to the registry may be dangerous",
    "description": ("Writing to the registry can have many system-level "
                    "consequences and requires careful review."),
    "signing_severity": "medium",
    "editors_only": True}}


def registry_key(write=False):
    """Represents a function which returns a registry key object."""
    res = {"return": lambda wrapper, arguments, traverser: (
        build_quick_xpcom("createInstance", "nsIWindowMediator",
                          traverser, wrapper=True))}
    if write:
        res.update(REGISTRY_WRITE)

    return res


INTERFACES = {
    u"nsISupports": {"value": {}},
    u"mozIStorageBaseStatement":
        {"value":
            {u"execute":
                {"dangerous": instanceactions.SYNCHRONOUS_SQL_DESCRIPTION},
             u"executeStep":
                {"dangerous": instanceactions.SYNCHRONOUS_SQL_DESCRIPTION}}},
    u"nsIExtensionManager": OBSOLETE_EXTENSION_MANAGER,
    u"nsIUpdateItem": OBSOLETE_EXTENSION_MANAGER,
    u"nsIInstallLocation": OBSOLETE_EXTENSION_MANAGER,
    u"nsIAddonInstallListener": OBSOLETE_EXTENSION_MANAGER,
    u"nsIAddonUpdateCheckListener": OBSOLETE_EXTENSION_MANAGER,
    u"imIUserStatusInfo":
        {"value":
            {u"setUserIcon": entity("imIUserStatusInfo.setUserIcon")}},
    u"nsICategoryManager":
        {"value": CATEGORY_MANAGER},
    u"nsIAbLDAPDirectory":
        {"value":
            {u"replicationFile": entity("nsIAbLDAPDirectory.replicationFile"),
             u"databaseFile": entity("nsIAbLDAPDirectory.databaseFile")}},
    u"nsIAbManager":
        {"value":
            {u"userProfileDirectory":
                entity("nsIAbManager.userProfileDirectory")}},
    u"nsIAccessibleRetrieval":
        {"dangerous":
            "Using the nsIAccessibleRetrieval interface causes significant "
            "performance degradation in Gecko. It should only be used in "
            "accessibility-related add-ons.",
         "value": {}},
    u"nsIBrowserSearchService":
        {"value":
            {u"currentEngine":
                {"readonly": search_warning(severity="high")},
             u"defaultEngine":
                {"readonly": search_warning(severity="high")},
             u"addEngine":
                {"dangerous": search_warning()},
             u"addEngineWithDetails":
                {"dangerous": search_warning()},
             u"removeEngine":
                {"dangerous": search_warning()},
             u"moveEngine":
                {"dangerous": search_warning()}}},

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
    u"nsIDNSService": {"value": {u"resolve": entity("nsIDNSService.resolve")}},
    u"nsIImapIncomingServer":
        {"value":
            {u"GetImapConnectionAndLoadUrl":
                {"return": call_definitions.TB12_nsIImapProtocol_changed}}},
    u"nsIImapMailFolderSink":
        {"value":
            {u"setUrlState":
                {"return": call_definitions.nsIImapMailFolderSink_changed},
             u"progressStatus": entity("nsIImapMailFolderSink.progressStatus")}},
    u"nsIImapProtocol":
        {"value":
            {u"NotifyHdrsToDownload":
                {"return": call_definitions.nsIImapProtocol_removed},
             u"Initialize":
                {"return": call_definitions.TB12_nsIImapProtocol_changed}}},
    u"nsIImportMail":
        {"value":
            {u"ImportMailbox": entity("nsIImportMail.ImportMailbox"),
             u"FindMailboxes": entity("nsIImportMail.FindMailboxes")}},
    u"nsIImportMailboxDescriptor":
        {"value":
            {u"file": entity("nsIImportMailboxDescriptor.file")}},
    u"nsIJSON":
        {"value":
            {u"encode":
                {"return": call_definitions.nsIJSON_deprec},
             u"decode":
                {"return": call_definitions.nsIJSON_deprec}}},
    u"nsIMailboxService":
        {"value":
            {u"ParseMailbox": entity("nsIMailboxService.ParseMailbox")}},
    u"nsIMailtoUrl":
        {"value":
            {u"GetMessageContents":
                {"return": call_definitions.nsIMailtoUrl_changed}}},
    u"nsIMessenger":
        {"value":
            {u"saveAttachmentToFolder":
                entity("nsIMessenger.saveAttachmentToFolder")}},
    u"nsIMsgAccountManager":
        {"value":
            {u"folderUriForPath": entity("nsIMsgAccountManager.folderUriForPath"),
             u"allIdentities": entity("nsIMsgAccountManager.allIdentities"),
             u"GetIdentitiesForServer": entity("nsIMsgAccountManager.GetIdentitiesForServer"),
             u"accounts": entity("nsIMsgAccountManager.accounts"),
             u"GetServersForIdentity": entity("nsIMsgAccountManager.GetServersForIdentity"),
             u"allServers": entity("nsIMsgAccountManager.allServers")}},
    u"nsIMsgLocalMailFolder":
        {"value":
            {u"addMessage":
                {"return": call_definitions.TB13_nsIMsgLocalMailFolder_changed},
             u"addMessageBatch":
                {"return": call_definitions.TB13_nsIMsgLocalMailFolder_changed}}},
    u"nsIMsgCloudFileProvider":
        {"value":
            {u"uploadFile": entity("nsIMsgCloudFileProvider.uploadFile"),
             u"urlForFile": entity("nsIMsgCloudFileProvider.urlForFile"),
             u"cancelFileUpload": entity("nsIMsgCloudFileProvider.cancelFileUpload"),
             u"deleteFile": entity("nsIMsgCloudFileProvider.deleteFile")}},
    u"nsIMsgDatabase":
        {"value":
            {u"Open":
                {"return": call_definitions.nsIMsgDatabase_changed}},
             u"openMailDBFromFile": entity("nsIMsgDatabase.openMailDBFromFile"),
             u"forceFolderDBClosed": entity("nsIMsgDatabase.forceFolderDBClosed"),
             u"checkAndPopulateRecipients": entity("nsIMsgDatabase.checkAndPopulateRecipients")},
    u"nsIMsgDBService":
      {"value":
        {u"openMailDBFromFile":
            {"return": call_definitions.nsIMsgDatabase_changed}}},
    u"nsIMsgFilterPlugin":
        {"value":
            {u"updateData": entity("nsIMsgFilterPlugin.updateData")}},
    u"nsIMsgFilterList":
        {"value":
            {u"defaultFile": entity("nsIMsgFilterList.defaultFile")}},
    u"nsIMsgFilterService":
        {"value":
            {u"OpenFilterList": entity("nsIMsgFilterService.OpenFilterList"),
             u"SaveFilterList": entity("nsIMsgFilterService.SaveFilterList"),
             u"applyFiltersToFolders": entity("nsIMsgFilterService.applyFiltersToFolders"),
             u"requiresCleanup": entity("nsIMsgFilterService.requiresCleanup"),
             u"clearRequiresCleanup": entity("nsIMsgFilterService.clearRequiresCleanup")}},
    u"nsIMsgFolder":
        {"value":
            {u"offlineStoreOutputStream":
                {"value": call_definitions.nsIMsgFolder_changed},
             u"filePath": entity("nsIMsgFolder.filePath"),
             u"getExpansionArray": entity("nsIMsgFolder.getExpansionArray"),
             u"ListDescendants": entity("nsIMsgFolder.ListDescendants"),
             u"knowsSearchNntpExtension": entity("nsIMsgFolder.knowsSearchNntpExtension"),
             u"allowsPosting": entity("nsIMsgFolder.allowsPosting")}},
    u"nsIMsgIdentity":
        {"value":
            {u"signature": entity("nsIMsgIdentity.signature")}},
    u"nsIMsgIncomingServer":
        {"value":
            {u"setDefaultLocalPath": entity("nsIMsgIncomingServer.setDefaultLocalPath"),
             u"getFileValue": entity("nsIMsgIncomingServer.getFileValue"),
             u"setFileValue": entity("nsIMsgIncomingServer.setFileValue"),
             u"localPath": entity("nsIMsgIncomingServer.localPath")}},
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
            {u"copyMessages": entity("nsIMsgPluggableStore.copyMessages"),
             u"getSummaryFile": entity("nsIMsgPluggableStore.getSummaryFile")}},
    u"nsIMsgProtocolInfo":
        {"value":
            {u"defaultLocalPath": entity("nsIMsgProtocolInfo.defaultLocalPath")}},
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
   u"nsIMsgSend":
        {"value":
            {u"tmpFile": entity("nsIMsgSend.tmpFile")}},
    u"nsIMsgThread":
        {"value":
            {u"GetChildAt":
                {"return": call_definitions.nsIMsgThread_removed}}},
    u"nsINoIncomingServer":
        {"value":
            {u"copyDefaultMessages":
                entity("nsINoIncomingServer.copyDefaultMessages")}},
    u"nsIObserverService":
        {"value":
            {u"addObserver":
                {"dangerous":
                    lambda a, t, e:
                        e.get_resource("em:bootstrap") and
                        "Authors of bootstrapped add-ons must take care "
                        "to remove any added observers "
                        "at shutdown."}},
         "dangerous": lambda a, t, e:
            lambda t, e: (
                e.metadata.get("is_jetpack") and
                "The observer service should not be used directly in SDK "
                "add-ons. Please use the 'sdk/system/events' module "
                "instead.")},
    u"nsIPrefBranch":
        {"value": {method: {"return": instanceactions.set_preference}
                   for method in (u"setBoolPref",
                                  u"setCharPref",
                                  u"setComplexValue",
                                  u"setIntPref")}},
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
    u"nsIRssIncomingServer":
        {"value":
            {u"subscriptionsDataSourcePath":
                entity("nsIRssIncomingServer.subscriptionsDataSourcePath"),
             u"feedItemsDataSourcePath":
                entity("nsIRssIncomingServer.feedItemsDataSourcePath")}},
    u"nsISound": {"value": {"play": entity("nsISound.play")}},
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
    u"nsITransferable":
        {"value":
            {u"init":
                entity("nsITransferable.init")}},
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
    u"nsIProtocolProxyService": {"value": {
        u"registerFilter": {"dangerous": {
            "err_id": ("testcases_javascript_actions",
                       "predefinedentities", "proxy_filter"),
            "description": (
                "Proxy filters can be used to direct arbitrary network "
                "traffic through remote servers, and may potentially "
                "be abused.",
                "Additionally, to prevent conflicts, the `applyFilter` "
                "method should always return its third argument in cases "
                "when it is not supplying a specific proxy."),
            "editors_only": True,
            "signing_severity": "low"}}}},
    u"nsIURLParser":
        {"value":
             {u"parsePath":
                  {"return": call_definitions.urlparser_parsepath_bug691588}}},
    u"nsIURL":
        {"value":
             {u"param":
                  {"value": call_definitions.url_param_bug691588}}},
    u"nsIUrlFetcher":
        {"value":
            {u"fireUrlRequest": entity("nsIUrlFetcher.fireUrlRequest"),
             u"initialize": entity("nsIUrlFetcher.initialize")}},
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
    u"nsIWebBrowserPersist":
        {"value":
             {u"saveChannel":
                  {"return": call_definitions.webbrowserpersist},
              u"saveURI":
                  {"return":
                       call_definitions.webbrowserpersist_saveuri},
              u"savePrivacyAwareURI":
                  {"return": call_definitions.webbrowserpersist}}},
    u"prplIAccount":
        {"value":
             {u"noNewlines": entity("prplIAccount.noNewlines"),
              u"maxMessageLength": entity("prplIAccount.maxMessageLength")}},
    u"nsIMsgCompFields":
        {"value":
             {u"newshost": entity("nsIMsgCompFields.newshost"),
              u"temporaryFiles": entity("nsIMsgCompFields.temporaryFiles")}},

    u"nsIMsgSearchAdapter":
        {"value":
             {u"CurrentUrlDone": entity("nsIMsgSearchAdapter.CurrentUrlDone")}},
    u"nsIMsgAccount":
        {"value":
             {u"identities": entity("nsIMsgAccount.identities")}},
    u"nsIMsgFilter":
        {"value":
             {u"getSortedActionList": entity("nsIMsgFilter.getSortedActionList"),
              u"actionList": entity("nsIMsgFilter.actionList")}},
    u"nsIMimeHeaders":
        {"value":
            {u"initialize": entity("nsIMimeHeaders.initialize")}},
    u"nsISmtpService":
        {"value":
            {u"GetSmtpServerByIdentity": entity("nsISmtpService.GetSmtpServerByIdentity"),
             u"smtpServers": entity("nsISmtpService.smtpServers"),
             u"createSmtpServer": entity("nsISmtpService.createSmtpServer"),
             u"deleteSmtpServer": entity("nsISmtpService.deleteSmtpServer")}},
    u"nsIMsgSend":
        {"value":
            {u"createAndSendMessage": entity("nsIMsgSend.createAndSendMessage"),
             u"createRFC822Message": entity("nsIMsgSend.createRFC822Message")}},
    u"nsIImportService":
        {"value":
            {u"CreateRFC822Message": entity("nsIImportService.CreateRFC822Message")}},
    u"nsIImapServerSink":
        {"value":
         {u"getImapStringByID": entity("nsIImapServerSink.getImapStringByID"),
          u"fEAlertWithID": entity("nsIImapServerSink.fEAlertWithID")}},
    u"nsIImportFieldMap":
        {"value":
         {u"SetFieldMapByDescription": entity("nsIImportFieldMap.SetFieldMapByDescription"),
          u"SetFieldValueByDescription": entity("nsIImportFieldMap.SetFieldValueByDescription"),
          u"GetFieldValue": entity("nsIImportFieldMap.GetFieldValue"),
          u"GetFieldValueByDescription": entity("nsIImportFieldMap.GetFieldValueByDescription")}},
    u"nsILocalMailIncomingServer":
        {"value":
         {u"createDefaultMailboxes": entity("nsILocalMailIncomingServer.createDefaultMailboxes")}},
    u"nsIAbLDAPAutoCompFormatter": entity("nsIAbLDAPAutoCompFormatter"),
    u"nsILDAPAutoCompFormatter": entity("nsILDAPAutoCompFormatter"),
    u"nsILDAPAutoCompleteSession": entity("nsILDAPAutoCompleteSession"),
    u"nsINewsBlogFeedDownloader":
        {"value":
             {u"updateSubscriptionsDS": entity("nsINewsBlogFeedDownloader.updateSubscriptionsDS")}},
    u"nsMsgFolderFlags":
        {"value":
             {u"NewsHost": entity("nsMsgFolderFlags.NewsHost")}},
    u"nsMsgFolderFlags":
        {"value":
             {u"Subscribed": entity("nsMsgFolderFlags.Subscribed")}},
    u"nsMsgFolderFlags":
        {"value":
             {u"ImapServer": entity("nsMsgFolderFlags.ImapServer")}},
    u"gMessageNotificationBar":
        {"value":
             {u"mBarStatus": entity("gMessageNotificationBar.mBarStatus")}},
    u"gMessageNotificationBar":
        {"value":
             {u"mBarFlagValues": entity("gMessageNotificationBar.mBarFlagValues")}},
    u"gMessageNotificationBar":
        {"value":
             {u"mMsgNotificationBar": entity("gMessageNotificationBar.mMsgNotificationBar")}},
    u"gMessageNotificationBar":
        {"value":
             {u"isFlagSet": entity("gMessageNotificationBar.isFlagSet")}},
    u"gMessageNotificationBar":
        {"value":
             {u"updateMsgNotificationBar": entity("gMessageNotificationBar.updateMsgNotificationBar")}},
    u"FeedUtils":
        {"value":
             {u"addFeed": entity("FeedUtils.addFeed")}},
    u"FeedUtils":
        {"value":
             {u"updateFolderFeedUrl": entity("FeedUtils.updateFolderFeedUrl")}},
    u"nsIMsgSearchTerm":
        {"value":
             {u"matchRfc822String": entity("nsIMsgSearchTerm.matchRfc822String")}},
    u"nsIMsgDBHdr":
        {"value":
             {u"setRecipientsArray": entity("nsIMsgDBHdr.setRecipientsArray")}},
    u"nsIMsgDBHdr":
        {"value":
             {u"setCCListArray": entity("nsIMsgDBHdr.setCCListArray")}},
    u"nsIMsgDBHdr":
        {"value":
             {u"setBCCListArray": entity("nsIMsgDBHdr.setBCCListArray")}},
    u"imICommand":
        {"value":
             {u"CONTEXT_IM": entity("imICommand.CONTEXT_IM")}},
    u"imICommand":
        {"value":
             {u"CONTEXT_CHAT": entity("imICommand.CONTEXT_CHAT")}},
    u"imICommand":
        {"value":
             {u"CONTEXT_ALL": entity("imICommand.CONTEXT_ALL")}},
    u"imICommand":
        {"value":
             {u"PRIORITY_LOW": entity("imICommand.PRIORITY_LOW")}},
    u"imICommand":
        {"value":
             {u"PRIORITY_DEFAULT": entity("imICommand.PRIORITY_DEFAULT")}},
    u"imICommand":
        {"value":
             {u"PRIORITY_PRPL": entity("imICommand.PRIORITY_PRPL")}},
    u"imICommand":
        {"value":
             {u"PRIORITY_HIGH": entity("imICommand.PRIORITY_HIGH")}},
    u"nsIImportAddressBooks":
        {"value":
             {u"FindAddressBooks": entity("nsIImportAddressBooks.FindAddressBooks")}},
    u"prplIConversation":
        {"value":
             {u"sendTyping": entity("prplIConversation.sendTyping")}},
    u"nsINewsBlogFeedDownloader":
        {"value":
             {u"downloadFeed": entity("nsINewsBlogFeedDownloader.downloadFeed")}},
    u"nsIMsgHeaderParser":
        {"value":
             {u"removeDuplicateAddresses": entity("nsIMsgHeaderParser.removeDuplicateAddresses")}},
    u"nsIMsgHeaderParser":
        {"value":
             {u"makeMimeAddress": entity("nsIMsgHeaderParser.makeMimeAddress")}},
    u"nsIMsgCompose":
        {"value":
             {u"checkAndPopulateRecipients": entity("nsIMsgCompose.checkAndPopulateRecipients")}},
    u"nsIFolderLookupService":
        {"value":
             {u"getFolderById": entity("nsIFolderLookupService.getFolderById")}},
    u"nsIAbCard":
        {"value":
             {u"kAllowRemoteContentProperty": entity("nsIAbCard.kAllowRemoteContentProperty")}},
    u"nsIAddrDatabase":
        {"value":
             {u"addAllowRemoteContent": entity("nsIAddrDatabase.addAllowRemoteContent")}},
    "nsICacheService": entity("nsICacheService"),
    "nsICacheSession": entity("nsICacheSession"),
    "nsICacheEntryDescriptor": entity("nsICacheEntryDescriptor"),
    "nsICacheListener": entity("nsICacheListener"),
    "nsICacheVisitor": entity("nsICacheVisitor"),

    "nsIWindowsRegKey": {"value": {u"create": REGISTRY_WRITE,
                                   u"createChild": registry_key(write=True),
                                   u"openChild": registry_key(),
                                   u"writeBinaryValue": REGISTRY_WRITE,
                                   u"writeInt64Value": REGISTRY_WRITE,
                                   u"writeIntValue": REGISTRY_WRITE,
                                   u"writeStringValue": REGISTRY_WRITE,
                                  }},
    }

INTERFACE_ENTITIES = {u"nsIXMLHttpRequest":
                          {"xpcom_map":
                               lambda: GLOBAL_ENTITIES["XMLHttpRequest"]},
                      u"nsIProcess": {"dangerous": {
                        "warning": "The use of nsIProcess is potentially "
                                   "dangerous and requires careful review "
                                   "by an administrative reviewer.",
                        "editors_only": True,
                        "signing_severity": "high",
                      }},
                      u"nsIDOMGeoGeolocation": {"dangerous":
                         "Use of the geolocation API by add-ons requires "
                         "prompting users for consent."},
                      u"nsIWindowsRegKey": {"dangerous": {
                          "signing_severity": "low",
                          "editors_only": True,
                          "description": (
                              "Access to the registry is potentially "
                              "dangerous, and should be reviewed with special "
                              "care.")}},
                      }

DANGEROUS_CERT_DB = {
    "err_id": ("javascript", "predefinedentities", "cert_db"),
    "description": "Access to the X509 certificate "
                   "database is potentially dangerous "
                   "and requires careful review by an "
                   "administrative reviewer.",
    "editors_only": True,
    "signing_severity": "high",
}

INTERFACE_ENTITIES.update(
    (interface, {"dangerous": DANGEROUS_CERT_DB})
    for interface in ("nsIX509CertDB", "nsIX509CertDB2", "nsIX509CertList",
                      "nsICertOverrideService"))

CONTRACT_ENTITIES = {
    contract: DANGEROUS_CERT_DB
    for contract in ("@mozilla.org/security/x509certdb;1",
                     "@mozilla.org/security/x509certlist;1",
                     "@mozilla.org/security/certoverride;1")}

for interface in INTERFACES:
    def construct(interface):
        def wrap():
            return INTERFACES[interface]
        return wrap
    if interface not in INTERFACE_ENTITIES:
        INTERFACE_ENTITIES[interface] = {}
    INTERFACE_ENTITIES[interface]["xpcom_map"] = construct(interface)


def build_quick_xpcom(method, interface, traverser, wrapper=False):
    """A shortcut to quickly build XPCOM objects on the fly."""
    extra = ()
    if isinstance(interface, (list, tuple)):
        interface, extra = interface[0], interface[1:]

    def interface_obj(iface):
        return traverser._build_global(
            name=method,
            entity={"xpcom_map":
                lambda: INTERFACES.get(iface, INTERFACES["nsISupports"])})

    constructor = xpcom_const(method, pretraversed=True)
    obj = constructor(None, [interface_obj(interface)], traverser)

    for iface in extra:
        # `xpcom_constructor` really needs to be cleaned up so we can avoid
        # this duplication.
        iface = interface_obj(iface)
        iface = traverser._build_global("QueryInterface",
                                        iface.value["xpcom_map"]())

        obj.value = obj.value.copy()

        value = obj.value["value"].copy()
        value.update(iface.value["value"])

        obj.value.update(iface.value)
        obj.value["value"] = value

    if isinstance(obj, JSWrapper) and not wrapper:
        obj = obj.value
    return obj


UNSAFE_TEMPLATE_METHOD = (
    "The use of `%s` can lead to unsafe "
    "remote code execution, and therefore must be done with "
    "great care, and only with sanitized data.")


SERVICES = {
    "appinfo": ("nsIXULAppInfo", "nsIXULRuntime"),
    "appShell": "nsIAppShellService",
    "blocklist": "nsIBlocklistService",
    "cache": "nsICacheService",
    "cache2": "nsICacheStorageService",
    "clipboard": "nsIClipboard",
    "console": "nsIConsoleService",
    "contentPrefs": "nsIContentPrefService",
    "cookies": ("nsICookieManager", "nsICookieManager2", "nsICookieService"),
    "dirsvc": ("nsIDirectoryService", "nsIProperties"),
    "DOMRequest": "nsIDOMRequestService",
    "domStorageManager": "nsIDOMStorageManager",
    "downloads": "nsIDownloadManager",
    "droppedLinkHandler": "nsIDroppedLinkHandler",
    "eTLD": "nsIEffectiveTLDService",
    "focus": "nsIFocusManager",
    "io": ("nsIIOService", "nsIIOService2"),
    "locale": "nsILocaleService",
    "logins": "nsILoginManager",
    "obs": "nsIObserverService",
    "perms": "nsIPermissionManager",
    "prefs": ("nsIPrefBranch2", "nsIPrefService", "nsIPrefBranch"),
    "prompt": "nsIPromptService",
    "scriptloader": "mozIJSSubScriptLoader",
    "scriptSecurityManager": "nsIScriptSecurityManager",
    "search": "nsIBrowserSearchService",
    "startup": "nsIAppStartup",
    "storage": "mozIStorageService",
    "strings": "nsIStringBundleService",
    "sysinfo": "nsIPropertyBag2",
    "telemetry": "nsITelemetry",
    "tm": "nsIThreadManager",
    "uriFixup": "nsIURIFixup",
    "urlFormatter": "nsIURLFormatter",
    "vc": "nsIVersionComparator",
    "wm": "nsIWindowMediator",
    "ww": "nsIWindowWatcher",
}

for key, value in SERVICES.items():
    SERVICES[key] = {"value": partial(build_quick_xpcom,
                                      "getService", value)}


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
    u"Services": {"value": SERVICES},

    u"AddonManager": {
        "readonly": False,
        "value": {
            u"autoUpdateDefault": {"readonly": SECURITY_PREF_MESSAGE},
            u"checkUpdateSecurity": {"readonly": SECURITY_PREF_MESSAGE},
            u"checkUpdateSecurityDefault": {"readonly": SECURITY_PREF_MESSAGE},
            u"updateEnabled": {"readonly": SECURITY_PREF_MESSAGE},
            u"getInstallForFile": ADDON_INSTALL_METHOD,
            u"getInstallForURL": ADDON_INSTALL_METHOD,
            u"installAddonsFromWebpage": ADDON_INSTALL_METHOD}},

    u"ctypes": {"dangerous": {
        "description": (
            "Insufficiently meticulous use of ctypes can lead to serious, "
            "and often exploitable, errors. The use of bundled binary code, "
            "or access to system libraries, may allow for add-ons to "
            "perform unsafe operations. All ctypes use must be carefully "
            "reviewed by a qualified reviewer."),
        "editors_only": True,
        "signing_severity": "high"}},

    u"document":
        {"value":
             {u"title":
                  {"overwriteable": True,
                   "readonly": False},
              u"defaultView":
                  {"value": lambda t: {"value": GLOBAL_ENTITIES}},
              u"getSelection":
                  {"return": call_definitions.document_getSelection},
              u"loadOverlay":
                  {"dangerous":
                       lambda a, t, e:
                           not a or not _get_as_str(t(a[0])).lower()
                               .startswith(("chrome:", "resource:"))},
              u"write": entity("document.write"),
              u"writeln": entity("document.write"),
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

    u"eval": {"dangerous": {"err_id": ("javascript", "dangerous_global",
                                       "eval"),
                            "signing_severity": "high"}},
    u"Function": {"dangerous": {"err_id": ("javascript", "dangerous_global",
                                           "eval"),
                                "signing_severity": "high"}},

    u"Object":
        {"value":
             {u"prototype": {"readonly": is_shared_scope},
              u"constructor":  # Just an experiment for now
                  {"value": lambda t: GLOBAL_ENTITIES["Function"]}}},
    u"String":
        {"value":
             {u"prototype": {"readonly": is_shared_scope}},
         "return": call_definitions.string_global},
    u"Array":
        {"value":
             {u"prototype": {"readonly": is_shared_scope}},
         "return": call_definitions.array_global},
    u"Number":
        {"value":
             {u"prototype":
                  {"readonly": is_shared_scope},
              u"POSITIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('inf'), traverser=t)},
              u"NEGATIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('-inf'), traverser=t)}},
         "return": call_definitions.number_global},
    u"Boolean":
        {"value":
             {u"prototype": {"readonly": is_shared_scope}},
         "return": call_definitions.boolean_global},
    u"RegExp": {"value": {u"prototype": {"readonly": is_shared_scope}}},
    u"Date": {"value": {u"prototype": {"readonly": is_shared_scope}}},
    u"File": {"value": {u"prototype": {"readonly": is_shared_scope}}},

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
                                      {"dangerous": {
                                          "signing_severity": "high",
                                          "description": (
                                            "enablePrivilege is extremely "
                                            "dangerous, and nearly always "
                                            "unnecessary. It should not be "
                                            "used under any circumstances."),
                                      }}}}}}}},
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
                                 {"dangerous": {
                                     "editors_only": "true",
                                     "signing_severity": "low"}},
                             u"cloneInto":
                                 {"dangerous": {
                                     "editors_only": True,
                                     "signing_severity": "low",
                                     "description": (
                                         "Can be used to expose privileged "
                                         "functionality to unprivileged scopes. "
                                         "Care should be taken to ensure that "
                                         "this is done safely.")}},
                             u"exportFunction":
                                 {"dangerous": {
                                     "editors_only": True,
                                     "signing_severity": "low",
                                     "description": (
                                         "Can be used to expose privileged "
                                         "functionality to unprivileged scopes. "
                                         "Care should be taken to ensure that "
                                         "this is done safely.")}},
                             u"import":
                                 {"dangerous":
                                      lambda a, t, e:
                                          a and "ctypes.jsm" in _get_as_str(t(a[0]))},

                             u"waiveXrays":
                                 {"return": call_definitions.js_unwrap}}},
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

    u"java": entity("java"),
    u"Packages": entity("Packages"),

    u"XPCOMUtils":
        {"value": {u"categoryManager": {"value": CATEGORY_MANAGER}}},
    u"gPropertiesButton": entity("gPropertiesButton"),
    u"gComposeButton": entity("gComposeButton"),
    u"onAbSearchReset": entity("onAbSearchReset"),
    u"startDebugger": entity("startDebugger"),
    u"stopDebugger": entity("stopDebugger"),
    u"onRecipientsInput": entity("onRecipientsInput"),
    u"kMsgNotificationPhishingBar": entity("kMsgNotificationPhishingBar"),
    u"kMsgNotificationJunkBar": entity("kMsgNotificationJunkBar"),
    u"kMsgNotificationRemoteImages": entity("kMsgNotificationRemoteImages"),
    u"kMsgNotificationMDN": entity("kMsgNotificationMDN"),
    u"gRemindLater": entity("gRemindLater"),
    u"onRecipientsInput": entity("onRecipientsInput"),
    u"gSendOrSaveOperationInProgress": entity("gSendOrSaveOperationInProgress"),
    u"ShowEditMessageBox": entity("ShowEditMessageBox"),
    u"ClearEditMessageBox": entity("ClearEditMessageBox"),
    u"updateCharsetPopupMenu": entity("updateCharsetPopupMenu"),
    u"EditorSetDocumentCharacterSet": entity("EditorSetDocumentCharacterSet"),
    u"DisablePhishingWarning": entity("DisablePhishingWarning"),
    u"RoomInfo": entity("RoomInfo"),
    u"FillInHTMLTooltip": entity("FillInHTMLTooltip"),
    u"escapeXMLchars": entity("escapeXMLchars"),
    u"getNonHtmlRecipients": entity("getNonHtmlRecipients"),
    u"updateCharsetPopupMenu": entity("updateCharsetPopupMenu"),
    u"EditorSetDocumentCharacterSet": entity("EditorSetDocumentCharacterSet"),
    u"awArrowHit": entity("awArrowHit"),
    u"UpdateMailEditCharset": entity("UpdateMailEditCharset"),
    u"InitCharsetMenuCheckMark": entity("InitCharsetMenuCheckMark"),
    u"allowRemoteContentForSender": entity("allowRemoteContentForSender"),
    u"allowRemoteContentForSite": entity("allowRemoteContentForSite"),
    u"createNewHeaderView": entity("createNewHeaderView"),
    u"getShortcutOrURIAndPostData": entity("getShortcutOrURIAndPostData"),

    # Common third-party libraries
    "Handlebars": {
        "value": {
            "SafeString":
                {"dangerous":
                    UNSAFE_TEMPLATE_METHOD % 'Handlebars.SafeString'}}},
    # Angular
    "$sce": {
        "value": {
            "trustAs": {"dangerous":
                            UNSAFE_TEMPLATE_METHOD % '$sce.trustAs'},
            "trustAsHTML": {"dangerous":
                                UNSAFE_TEMPLATE_METHOD % '$sce.trustAsHTML'}}},
}

CONTENT_DOCUMENT = GLOBAL_ENTITIES[u"content"]["value"][u"document"]
