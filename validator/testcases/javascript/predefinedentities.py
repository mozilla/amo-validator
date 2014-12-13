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
    u"newThread": "Creating threads from JavaScript is a common cause "
                  "of crashes and is unsupported in recent versions of the platform",
    u"processNextEvent": "Spinning the event loop with processNextEvent is a common "
                         "cause of deadlocks, crashes, and other errors due to "
                         "unintended reentrancy. Please use asynchronous callbacks "
                         "instead wherever possible",
}

CUSTOMIZATION_PREF_MESSAGE = (
    "Extensions must not alter user preferences such as the current home "
    "page, new tab page, or search engine, without explicit user consent, "
    "in which a user takes a non-default action. Such changes must also "
    "be reverted when the extension is disabled or uninstalled.")

BANNED_PREF_BRANCHES = (
    (u"browser.newtab.url", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.newtabpage.enabled", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.preferences.instantApply", None),
    (u"browser.search.defaultenginename", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.search.searchEnginesURL", CUSTOMIZATION_PREF_MESSAGE),
    (u"browser.startup.homepage", CUSTOMIZATION_PREF_MESSAGE),
    (u"capability.policy.", None),
    (u"extensions.alwaysUnpack", None),
    (u"extensions.blocklist.", None),
    (u"extensions.bootstrappedAddons", None),
    (u"extensions.checkCompatibility", None),
    (u"extensions.dss.", None),
    (u"extensions.getAddons.", None),
    (u"extensions.getMoreThemesURL", None),
    (u"extensions.installCache", None),
    (u"extensions.lastAppVersion", None),
    (u"extensions.pendingOperations", None),
    (u"extensions.update.", None),
    (u"general.useragent.", None),
    (u"keyword.URL", CUSTOMIZATION_PREF_MESSAGE),
    (u"keyword.enabled", CUSTOMIZATION_PREF_MESSAGE),
    (u"network.proxy.autoconfig_url",
        "As many add-ons have reason to change the proxy autoconfig URL, and "
        "only one at a time may do so without conflict, extensions must "
        "make proxy changes using other mechanisms. Installing a proxy "
        "filter is the recommended alternative: "
        "https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XPCOM/"
        "Reference/Interface/nsIProtocolProxyService#registerFilter()"),
    (u"network.http.", None),
    (u"network.websocket.", None),
    (u"nglayout.debug.disable_xul_cache", None),
)

BANNED_PREF_REGEXPS = [
    r"extensions\..*\.update\.(url|enabled|interval)",
]


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

INTERFACES = {
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
    }

INTERFACE_ENTITIES = {u"nsIXMLHttpRequest":
                          {"xpcom_map":
                               lambda: GLOBAL_ENTITIES["XMLHttpRequest"]},
                      u"nsIProcess": {"dangerous": {
                        "warning": "The use of nsIProcess is potentially "
                                   "dangerous and requires careful review "
                                   "by an administrative reviewer.",
                        "editors_only": True,
                      }},
                      u"nsIDOMGeoGeolocation": {"dangerous":
                         "Use of the geolocation API by add-ons requires "
                         "prompting users for consent."},
                      u"nsIX509CertDB": {"dangerous": {
                          "description": "Access to the X509 certificate "
                                         "database is potentially dangerous "
                                         "and requires careful review by an "
                                         "administrative reviewer.",
                          "editors_only": True,
                      }}}
for interface in INTERFACES:
    def construct(interface):
        def wrap():
            return INTERFACES[interface]
        return wrap
    INTERFACE_ENTITIES[interface] = {"xpcom_map": construct(interface)}


def build_quick_xpcom(method, interface, traverser, wrapper=False):
    """A shortcut to quickly build XPCOM objects on the fly."""
    constructor = xpcom_const(method, pretraversed=True)
    interface_obj = traverser._build_global(
                        name=method,
                        entity={"xpcom_map": lambda: INTERFACES[interface]})
    obj = constructor(None, [interface_obj], traverser)
    if isinstance(obj, JSWrapper) and not wrapper:
        obj = obj.value
    return obj


UNSAFE_TEMPLATE_METHOD = (
    "The use of `%s` can lead to unsafe "
    "remote code execution, and therefore must be done with "
    "great care, and only with sanitized data.")


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
        {"value":
            {u"wm":
                {"value":
                    lambda t: build_quick_xpcom(
                        "getService", "nsIWindowMediator", t)},
             u"ww":
                {"value":
                    lambda t: build_quick_xpcom(
                        "getService", "nsIWindowWatcher", t)}}},

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
                           not a or _get_as_str(t(a[0])).lower() == "script"
                           and "Dynamic creation of script nodes can be "
                               "unsafe if contents are not static or are "
                               "otherwise unsafe, or if `src` is remote."},
              u"createElementNS":
                  {"dangerous":
                       lambda a, t, e:
                           not a or _get_as_str(t(a[0])).lower() == "script"
                           and "Dynamic creation of script nodes can be "
                               "unsafe if contents are not static or are "
                               "otherwise unsafe, or if `src` is remote."},
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
