from call_definitions import open_in_chrome_context
from instanceproperties import _set_HTML_property
from validator.compat import (FX10_DEFINITION, FX14_DEFINITION,
                              FX16_DEFINITION, FX31_DEFINITION,
                              FX32_DEFINITION, FX33_DEFINITION,
                              TB14_DEFINITION, TB15_DEFINITION,
                              TB16_DEFINITION, TB18_DEFINITION,
                              TB19_DEFINITION, TB20_DEFINITION,
                              TB21_DEFINITION, TB22_DEFINITION,
                              TB24_DEFINITION, TB25_DEFINITION,
                              TB26_DEFINITION, TB27_DEFINITION,
                              TB28_DEFINITION, TB29_DEFINITION,
                              TB30_DEFINITION, TB31_DEFINITION)
from validator.constants import BUGZILLA_BUG


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(func):
        ENTITIES[name] = func
        return func
    return wrap


def entity(name, result=None):
    def return_wrap(t):
        output = ENTITIES[name](traverser=t)
        if result is not None:
            return result
        elif output is not None:
            return output
        else:
            return {"value": {}}
    return {"value": return_wrap}


def deprecated_entity(name, version, message, bug, status="deprecated",
                      compat_type="error"):
    def wrap(traverser):
        traverser.err.warning(
            err_id=("js", "entities", name),
            warning="`%s` has been %s." % (name, status),
            description=[message,
                         "See %s for more information." % BUGZILLA_BUG % bug],
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context,
            for_appversions=version,
            compatibility_type=compat_type,
            tier=5)
    register_entity(name)(wrap)

def register_changed_entities(version_definition, entities, version_string):
    for entity in entities:
        deprecated_entity(
            name=entity["name"],
            version=version_definition,
            message="The method or property `%s` has been `%s` in `%s`."
                % (entity["name"], entity["status"], version_string),
            bug=entity["bug"],
            compat_type=entity["compat_type"])

DEP_IHF_MESSAGE = ("The `importHTMLFromFile` and `importHTMLFromURI` functions "
                   "have been removed from the `nsIPlacesImportExportService` "
                   "interface. You can use the equivalent functions in the "
                   "`BookmarkHTMLUtils` module instead.")
deprecated_entity(name="importHTMLFromFile", version=FX14_DEFINITION,
                  message=DEP_IHF_MESSAGE, bug=482911)
deprecated_entity(name="importHTMLFromURI", version=FX14_DEFINITION,
                  message=DEP_IHF_MESSAGE, bug=482911)

JAVA_MESSAGE = "The global variables related to Java have been removed."
deprecated_entity(name="java", version=FX16_DEFINITION,
                  message=JAVA_MESSAGE, bug=748343)
deprecated_entity(name="Packages", version=FX16_DEFINITION,
                  message=JAVA_MESSAGE, bug=748343)


DOC_WRITE_MSG = ("https://developer.mozilla.org/docs/XUL/School_tutorial/"
                 "DOM_Building_and_HTML_Insertion")

@register_entity("document.write")
def document_write(traverser):
    def on_write(wrapper, arguments, traverser):
        traverser.err.warning(
            err_id=("js", "document.write", "evil"),
            warning="Use of `document.write` strongly discouraged.",
            description=["`document.write` will fail in many circumstances ",
                         "when used in extensions, and has potentially severe "
                         "security repercussions when used improperly. "
                         "Therefore, it should not be used. See %s for more "
                         "information." % DOC_WRITE_MSG],
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)
        if not arguments:
            return
        value = traverser._traverse_node(arguments[0])
        _set_HTML_property('document.write()', value, traverser)

    return {"return": on_write}


@register_entity("document.xmlEncoding")
def xmlEncoding(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlEncoding"),
        error="xmlEncoding removed in Gecko 10.",
        description='The "xmlEncoding" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("document.xmlVersion")
def xmlVersion(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlVersion"),
        error="xmlVersion removed in Gecko 10.",
        description='The "xmlVersion" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("document.xmlStandalone")
def xmlStandalone(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlStandalone"),
        error="xmlStandalone removed in Gecko 10.",
        description='The "xmlStandalone" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsIDNSService.resolve")
def nsIDNSServiceResolve(traverser):
    traverser.err.warning(
        err_id=("testcases_javascript_entity_values",
                "nsIDNSServiceResolve"),
        warning="`nsIDNSService.resolve()` should not be used.",
        description="The `nsIDNSService.resolve` method performs a "
                    "synchronous DNS lookup, which will freeze the UI. This "
                    "can result in severe performance issues. "
                    "`nsIDNSService.asyncResolve()` should be used instead.",
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity("nsIDOMNSHTMLElement")
def nsIDOMNSHTMLElement(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values",
                "nsIDOMNSHTMLFrameElement"),
        error="nsIDOMNSHTMLElement interface removed in Gecko 10.",
        description='The "nsIDOMNSHTMLElement" interface has been removed. '
                    'You can use nsIDOMHTMLFrameElement instead. See %s for '
                    'more information.' % BUGZILLA_BUG % 684821,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsIDOMNSHTMLFrameElement")
def nsIDOMNSHTMLFrameElement(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values",
                "nsIDOMNSHTMLFrameElement"),
        error="nsIDOMNSHTMLFrameElement interface removed in Gecko 10.",
        description='The "nsIDOMNSHTMLFrameElement" interface has been '
                    'removed. You can use nsIDOMHTMLFrameElement instead. See '
                    '%s for more information.' % BUGZILLA_BUG % 677085,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsISound.play")
def nsISoundPlay(traverser):
    traverser.err.warning(
        err_id=("testcases_javascript_entity_values",
                "nsISound_play"),
        warning="`nsISound.play` should not be used.",
        description="The `nsISound.play` function is synchronous, and thus "
                    "freezes the interface while the sound is playing. It "
                    "should be avoided in favor of the HTML5 audio APIs.",
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity("nsIBrowserHistory.lastPageVisited")
def nsIBrowserHistory(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values",
                "nsIBrowserHistory_lastPageVisited"),
        error="lastPageVisited property has been removed in Gecko 10.",
        description='The "lastPageVisited" property has been removed. See %s '
                    'for more information.' % BUGZILLA_BUG % 691524,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsIDOMHTMLDocument")
def queryCommandText(traverser):
    traverser.err.warning(
        err_id=("testcases_javascript_entity_values",
                "nsIDOMHTMLDocument"),
        warning="`queryCommandText` and `execCommandShowHelp` removed.",
        description="The `queryCommandText` and `execCommandShowHelp` methods "
                    "have been removed from the `nsIDOMHTMLDocument` interface "
                    "in Gecko 14. See %s for more information." %
                        BUGZILLA_BUG % 742261,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX14_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsIWindowWatcher.openWindow")
def nsIWindowWatcher_openWindow(traverser):
    def on_open(wrapper, arguments, traverser):
        if not arguments:
            return
        uri = traverser._traverse_node(arguments[0])
        open_in_chrome_context(uri, "nsIWindowWatcher.openWindow", traverser)

    return {"return": on_open}


@register_entity("nsITransferable.init")
def nsITransferable_init(traverser):
    def on_init(wrapper, arguments, traverser):
        if not arguments:
            return
        first_arg = traverser._traverse_node(arguments[0])
        if first_arg.get_literal_value():
            return
        traverser.err.warning(
            err_id=("js_entity_values", "nsITransferable", "init"),
            warning="`init` should not be called with a null first argument",
            description="Calling `nsITransferable.init()` with a null first "
                        "argument has the potential to leak data across "
                        "private browsing mode sessions. `null` is  "
                        "appropriate only when reading data or writing data "
                        "which is not associated with a particular window.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)

    return {"return": on_init}


# Thunderbird 14 IDL changes
@register_entity("nsIMsgPluggableStore.copyMessages")
def nsIMsgPluggableStore_copyMessages(traverser):
    traverser.err.notice(
        err_id=("testcases_javascript_entity_values",
                "nsIMsgPluggableStore_copyMessages"),
        notice="Altered nsIMsgPluggableStore.copyMessages method in use.",
        description="This add-on uses nsIMsgPluggableStore.copyMessages "
                    "which was changed "
                    "in Thunderbird 14. For more information, please refer to "
                    "%s." % BUGZILLA_BUG % 738651,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB14_DEFINITION,
        compatibility_type="error",
        tier=5)


# Thunderbird 15 IDL changes
@register_entity("nsIImportMail.ImportMailbox")
def nsIImportMail_ImportMailbox(traverser):
    traverser.err.notice(
        err_id=("testcases_javascript_entity_values",
                "nsIImportMail_ImportMailbox"),
        notice="Altered `nsIImportMail.ImportMailbox` method in use.",
        description="This add-on uses `nsIImportMail.ImportMailbox` "
                    "which had its second parameter changed from `nsIFile` "
                    "to `nsIMsgFolder` in Thunderbird 15. Please refer to: "
                    "%s." % BUGZILLA_BUG % 729676,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB15_DEFINITION,
        compatibility_type="error",
        tier=5)


# Thunderbird 16 IDL changes
TB16_METHODS = {
    "imIUserStatusInfo.setUserIcon": "aIconFile",
    "nsIMsgCloudFileProvider.uploadFile": "aFile",
    "nsIMsgCloudFileProvider.urlForFile": "aFile",
    "nsIMsgCloudFileProvider.cancelFileUpload": "aFile",
    "nsIMsgCloudFileProvider.deleteFile": "aFile",
    "nsIMessenger.saveAttachmentToFolder": "aDestFolder",
    "nsIMsgAccountManager.folderUriForPath": "aLocalPath",
    "nsIMsgIncomingServer.setDefaultLocalPath": "aDefaultLocalPath",
    "nsIMsgIncomingServer.getFileValue": "return type",
    "nsIMsgIncomingServer.setFileValue": "aValue",
    "nsIMsgPluggableStore.getSummaryFile": "aFolder",
    "nsIMsgFilterPlugin.updateData": "aFile",
    "nsIMsgFilterService.OpenFilterList": "filterFile",
    "nsIMsgFilterService.SaveFilterList": "filterFile",
    "nsIURLFetcher.fireURLRequest": "localFile",
    "nsIURLFetcher.initialize": "localFIle",
    "nsIMsgDatabase.openMailDBFromFile": "aFile",
    "nsIMailboxService.ParseMailbox": "aMailboxPath",
    "nsINoIncomingServer.copyDefaultMessages": "parentDir",
}

for func, param in TB16_METHODS.items():
    deprecated_entity(
        name=func, version=TB16_DEFINITION,
        message="The `%s` parameter has been changed from `nsILocalFile` to "
                "`nsIFile`" % param,
        bug=749930)

TB16_ATTRIBUTES = [
    "nsIAbLDAPDirectory.replicationFile",
    "nsIAbLDAPDirectory.databaseFile",
    "nsIAbManager.userProfileDirectory",
    "nsIMsgFolder.filePath",
    "nsIMsgIdentity.signature",
    "nsIMsgIncomingServer.localPath",
    "nsIMsgProtocolInfo.defaultLocalPath",
    "nsIMsgFilterList.defaultFile",
    "nsIMsgSend.tmpFile",
    "nsIImportMailboxDescriptor.file",
    "nsIRssIncomingServer.subscriptionsDataSourcePath",
    "nsIRssIncomingServer.feedItemsDataSourcePath",
]

for attrib in TB16_ATTRIBUTES:
    deprecated_entity(
        name=attrib, version=TB16_DEFINITION,
        message="This attribute has been changed from `nsILocalFile` to "
                "`nsIFile`",
        bug=749930)

# Thunderbird 18 IDL changes
@register_entity("prplIAccount.noNewlines")
def prplIAccount_noNewlines(traverser):
    traverser.err.notice(
        err_id=("testcases_javascript_entity_values",
                "prplIAccount_noNewlines"),
        notice="Altered `prplIAccount.noNewlines` method in use.",
        description="This add-on uses the `prplIAccount.noNewlines` property "
                    "which has been removed in `%s`." % BUGZILLA_BUG % 799068,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB18_DEFINITION,
        compatibility_type="error",
        tier=5)

# Thunderbird 19 IDL changes
TB19_ENTITIES = [
    {"name":"nsIMsgCompFields.newshost",
     "status": "changed",
     "bug": 133605,
     "compat_type": "error"},
    {"name": "nsIMsgSearchAdapter.CurrentUrlDone",
     "status": "changed",
     "bug": 801383,
     "compat_type": "error"}
]
register_changed_entities(version_definition=TB19_DEFINITION,
    entities=TB19_ENTITIES, version_string="Thunderbird 19")

# Thunderbird 20 IDL changes
TB20_ENTITIES = [
    {"name": "nsIMsgAccount.identities",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgAccountManager.allIdentities",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgAccountManager.GetIdentitiesForServer",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgAccountManager.accounts",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgAccountManager.GetServersForIdentity",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgAccountManager.allServers",
     "status": "changed", "bug": 820377, "compat_type": "error"},
    {"name": "nsIMsgFolder.getExpansionArray",
     "status": "removed", "bug": 821236, "compat_type": "error"},
    {"name": "nsIMsgFilter.getSortedActionList",
     "status": "changed", "bug": 821253, "compat_type": "error"},
    {"name": "nsIMsgFilter.actionList",
     "status": "removed", "bug": 821743, "compat_type": "error"},
    {"name": "nsIMsgFilterService.applyFiltersToFolders",
     "status": "changed", "bug": 822131, "compat_type": "error"}
]
register_changed_entities(version_definition=TB20_DEFINITION,
    entities=TB20_ENTITIES, version_string="Thunderbird 20")

# Thunderbird 21 IDL changes
TB21_ENTITIES = [
    {"name":"nsIMimeHeaders.initialize",
     "status": "removed",
     "bug": 790852,
     "compat_type": "error"},
    {"name": "nsIMsgFolder.ListDescendants",
     "status": "removed",
     "bug": 436089,
     "compat_type": "error"}
]
register_changed_entities(version_definition=TB21_DEFINITION,
    entities=TB21_ENTITIES, version_string="Thunderbird 21")

# Thunderbird 22 IDL changes
TB22_ENTITIES = [
    {"name":"nsISmtpService.GetSmtpServerByIdentity",
     "status": "renamed to getServerByIdentity",
     "bug": 681219,
     "compat_type": "error"},
    {"name":"nsISmtpService.smtpServers",
     "status": "renamed to servers",
     "bug": 681219,
     "compat_type": "error"},
    {"name":"nsISmtpService.createSmtpServer",
     "status": "renamed to createServer",
     "bug": 681219,
     "compat_type": "error"},
    {"name":"nsISmtpService.deleteSmtpServer",
     "status": "renamed to deleteServer",
     "bug": 681219,
     "compat_type": "error"},
    {"name":"nsIMimeConverter.encodeMimePartIIStr",
     "status": "removed",
     "bug": 834757,
     "compat_type": "error"},
    {"name":"nsIMsgSend.createAndSendMessage",
     "status": "changed",
     "bug": 737519,
     "compat_type": "error"},
    {"name":"nsIMsgSend.createRFC822Message",
     "status": "changed",
     "bug": 737519,
     "compat_type": "error"},
    {"name":"nsIImportService.CreateRFC822Message",
     "status": "changed",
     "bug": 737519,
     "compat_type": "error"},
    {"name":"nsIMsgFolder.requiresCleanup",
     "status": "removed",
     "bug": 544621,
     "compat_type": "error"},
    {"name":"nsIMsgFolder.clearRequiresCleanup",
     "status": "removed",
     "bug": 544621,
     "compat_type": "error"}
]
register_changed_entities(version_definition=TB22_DEFINITION,
    entities=TB22_ENTITIES, version_string="Thunderbird 22")

# Thunderbird 24 IDL changes
TB24_ENTITIES = [
    {"name":"nsIMsgFolder.knowsSearchNntpExtension",
     "status": "removed",
     "bug": 882502,
     "compat_type": "error"},
    {"name":"nsIMsgFolder.allowsPosting",
     "status": "removed",
     "bug": 882502,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB24_DEFINITION,
    entities=TB24_ENTITIES, version_string="Thunderbird 24")

# Thunderbird 25 IDL changes
TB25_ENTITIES = [
    {"name":"nsIImapMailFolderSink.progressStatus",
     "status": "renamed to nsIImapMailFolderSink.progressStatusString",
     "bug": 551919,
     "compat_type": "error"},
    {"name":"nsIImapServerSink.getImapStringByID",
     "status": "renamed to nsIImapServerSink.getImapStringByName",
     "bug": 551919,
     "compat_type": "error"},
    {"name":"nsIImapServerSink.fEAlertWithID",
     "status": "renamed to nsIImapServerSink.fEAlertWithName",
     "bug": 551919,
     "compat_type": "error"},
    {"name":"nsIMsgCompFields.temporaryFiles",
     "status": "removed",
     "bug": 889031,
     "compat_type": "error"},
    {"name":"nsIImportFieldMap.SetFieldMapByDescription",
     "status": "removed",
     "bug": 891271,
     "compat_type": "error"},
    {"name":"nsIImportFieldMap.SetFieldValueByDescription",
     "status": "removed",
     "bug": 891271,
     "compat_type": "error"},
    {"name":"nsIImportFieldMap.GetFieldValue",
     "status": "removed",
     "bug": 891271,
     "compat_type": "error"},
    {"name":"nsIImportFieldMap.GetFieldValueByDescription",
     "status": "removed",
     "bug": 891271,
     "compat_type": "error"},
    {"name":"nsILocalMailIncomingServer.createDefaultMailboxes",
     "status": "changed",
     "bug": 886112,
     "compat_type": "error"},
    {"name":"nsINoIncomingServer.copyDefaultMessages",
     "status": "changed",
     "bug": 886112,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB25_DEFINITION,
    entities=TB25_ENTITIES, version_string="Thunderbird 25")

@register_entity("nsIAbLDAPAutoCompFormatter")
def nsIAbLDAPAutoCompFormatter(traverser):
    traverser.err.error(
        err_id=("testcases_idl_removed_interface"),
        error="nsIAbLDAPAutoCompFormatter interface has been removed in Thunderbird 25.",
        description='The "nsIAbLDAPAutoCompFormatter" interface has been removed. '
                    'See %s for more information.' % BUGZILLA_BUG % 452232,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB25_DEFINITION,
        compatibility_type="error",
        tier=5)

@register_entity("nsILDAPAutoCompFormatter")
def nsILDAPAutoCompFormatter(traverser):
    traverser.err.error(
        err_id=("testcases_idl_removed_interface"),
        error="nsILDAPAutoCompFormatter interface has been removed in Thunderbird 25.",
        description='The "nsILDAPAutoCompFormatter" interface has been removed. '
                    'See %s for more information.' % BUGZILLA_BUG % 452232,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB25_DEFINITION,
        compatibility_type="error",
        tier=5)

@register_entity("nsILDAPAutoCompleteSession")
def nsILDAPAutoCompleteSession(traverser):
    traverser.err.error(
        err_id=("testcases_idl_removed_interface"),
        error="nsILDAPAutoCompleteSession interface removed in Thunderbird 25.",
        description='The "nsILDAPAutoCompleteSession" interface has been removed. '
                    'See %s for more information.' % BUGZILLA_BUG % 452232,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=TB25_DEFINITION,
        compatibility_type="error",
        tier=5)


# Thunderbird 26 JS globals changes
deprecated_entity(name="gPropertiesButton", version=TB26_DEFINITION,
                  message="The global object `gPropertiesButton` has been removed.", bug=749564)
deprecated_entity(name="gComposeButton", version=TB26_DEFINITION,
                  message="The global object `gComposeButton` has been removed.", bug=749564)
deprecated_entity(name="onAbSearchReset", version=TB26_DEFINITION,
                  message="The global object `onAbSearchReset` has been removed.", bug=749564)

# Thunderbird 27 JS globals changes
deprecated_entity(name="startDebugger", version=TB27_DEFINITION,
                  message="The global object `startDebugger` has been removed.", bug=884805)
deprecated_entity(name="stopDebugger", version=TB27_DEFINITION,
                  message="The global object `stopDebugger` has been removed.", bug=884805)

# Thunderbird 28 IDL changes
TB28_ENTITIES = [
    {"name":"nsINewsBlogFeedDownloader.updateSubscriptionsDS",
     "status": "changed",
     "bug": 934316,
     "compat_type": "error"},
    {"name":"nsMsgFolderFlags.NewsHost",
     "status": "removed",
     "bug": 858993,
     "compat_type": "error"},
    {"name":"nsMsgFolderFlags.Subscribed",
     "status": "removed",
     "bug": 858993,
     "compat_type": "error"},
    {"name":"nsMsgFolderFlags.ImapServer",
     "status": "removed",
     "bug": 858993,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB28_DEFINITION,
    entities=TB28_ENTITIES, version_string="Thunderbird 28")

# Thunderbird 28 JS changes
TB28_JS_ENTITIES = [
    {"name":"gMessageNotificationBar.mBarStatus",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"gMessageNotificationBar.mBarFlagValues",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"gMessageNotificationBar.mMsgNotificationBar",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"gMessageNotificationBar.isFlagSet",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"gMessageNotificationBar.updateMsgNotificationBar",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"FeedUtils.addFeed",
     "status": "changed",
     "bug": 934316,
     "compat_type": "error"},
    {"name":"FeedUtils.updateFolderFeedUrl",
     "status": "removed",
     "bug": 934316,
     "compat_type": "error"},
    {"name":"kMsgNotificationPhishingBar",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"kMsgNotificationJunkBar",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"kMsgNotificationRemoteImages",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"kMsgNotificationMDN",
     "status": "removed",
     "bug": 562048,
     "compat_type": "error"},
    {"name":"gRemindLater",
     "status": "removed",
     "bug": 521158,
     "compat_type": "error"},
    {"name":"onRecipientsInput",
     "status": "renamed to onRecipientsChanged",
     "bug": 933101,
     "compat_type": "error"},
    {"name":"gSendOrSaveOperationInProgress",
     "status": "removed",
     "bug": 793270,
     "compat_type": "error"},
    {"name":"ShowEditMessageBox",
     "status": "removed",
     "bug": 939982,
     "compat_type": "error"},
    {"name":"ClearEditMessageBox",
     "status": "removed",
     "bug": 939982,
     "compat_type": "error"},
    {"name":"updateCharsetPopupMenu",
     "status": "renamed to EditorUpdateCharsetMenu",
     "bug": 943732,
     "compat_type": "error"},
    {"name":"EditorSetDocumentCharacterSet",
     "status": "renamed to EditorSetCharacterSet",
     "bug": 943732,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB28_DEFINITION,
    entities=TB28_JS_ENTITIES, version_string="Thunderbird 28")

# Thunderbird 29 IDL changes
TB29_ENTITIES = [
    {"name":"nsIMsgSearchTerm.matchRfc822String",
     "status": "changed",
     "bug": 842632,
     "compat_type": "error"},
    {"name":"nsIMsgDBHdr.setRecipientsArray",
     "status": "removed",
     "bug": 842632,
     "compat_type": "error"},
    {"name":"nsIMsgDBHdr.setCCListArray",
     "status": "removed",
     "bug": 842632,
     "compat_type": "error"},
    {"name":"nsIMsgDBHdr.setBCCListArray",
     "status": "removed",
     "bug": 842632,
     "compat_type": "error"},
    {"name":"prplIAccount.maxMessageLength",
     "status": "removed",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.CONTEXT_IM",
     "status": "renamed to CMD_CONTEXT_IM",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.CONTEXT_CHAT",
     "status": "renamed to CMD_CONTEXT_CHAT",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.CONTEXT_ALL",
     "status": "renamed to CMD_CONTEXT_ALL",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.PRIORITY_LOW",
     "status": "renamed to CMD_PRIORITY_LOW",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.PRIORITY_DEFAULT",
     "status": "renamed to CMD_PRIORITY_DEFAULT",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.PRIORITY_PRPL",
     "status": "renamed to CMD_PRIORITY_PRPL",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"imICommand.PRIORITY_HIGH",
     "status": "renamed to CMD_PRIORITY_HIGH",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"nsIImportAddressBooks.FindAddressBooks",
     "status": "changed",
     "bug": 945045,
     "compat_type": "error"},
    {"name":"nsIImportMail.FindMailboxes",
     "status": "changed",
     "bug": 945045,
     "compat_type": "error"},
    {"name":"prplIConversation.sendTyping",
     "status": "changed",
     "bug": 954484,
     "compat_type": "error"},
    {"name":"nsINewsBlogFeedDownloader.downloadFeed",
     "status": "changed",
     "bug": 959272,
     "compat_type": "error"},
    {"name":"nsIMsgHeaderParser.removeDuplicateAddresses",
     "status": "removed",
     "bug": 842632,
     "compat_type": "error"},
    {"name":"nsIMsgHeaderParser.makeMimeAddress",
     "status": "removed",
     "bug": 842632,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB29_DEFINITION,
    entities=TB29_ENTITIES, version_string="Thunderbird 29")

# Thunderbird 29 JS changes
TB29_JS_ENTITIES = [
    {"name":"DisablePhishingWarning",
     "status": "",
     "bug": 926473,
     "compat_type": "error"},
    {"name":"RoomInfo",
     "status": "",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"FillInHTMLTooltip",
     "status": "",
     "bug": 956586,
     "compat_type": "error"},
    {"name":"escapeXMLchars",
     "status": "",
     "bug": 942638,
     "compat_type": "error"},
    {"name":"gPluginHandler.isTooSmall",
     "status": "removed",
     "bug": 951800,
     "compat_type": "error"},
    {"name":"XMPPSession.authDialog",
     "status": "removed",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"XMPPMUCConversation.supportChatStateNotifications",
     "status": "removed",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"Socket.inputSegmentSize",
     "status": "removed",
     "bug": 920801,
     "compat_type": "error"},
    {"name":"XMPPMUCConversationPrototype.normalizedName",
     "status": "removed",
     "bug": 957918,
     "compat_type": "error"},
    {"name":"XMPPAccountBuddyPrototype.normalizedName",
     "status": "removed",
     "bug": 957918,
     "compat_type": "error"},
    {"name":"XMPPAccountPrototype.normalizedName",
     "status": "removed",
     "bug": 957918,
     "compat_type": "error"},
    {"name":"GenericAccountPrototype.maxMessageLength",
     "status": "removed",
     "bug": 954484,
     "compat_type": "error"},
    {"name":"mailTabType.desiredColumnStates",
     "status": "removed",
     "bug": 528044,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB29_DEFINITION,
    entities=TB29_JS_ENTITIES, version_string="Thunderbird 29")

# Thunderbird 30 IDL changes
TB30_ENTITIES = [
    {"name":"nsIMsgDatabase.forceFolderDBClosed",
     "status": "moved to nsIMsgDBService",
     "bug": 876548,
     "compat_type": "error"},
    {"name":"nsIMsgCompose.checkAndPopulateRecipients",
     "status": "removed",
     "bug": 970118,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB30_DEFINITION,
    entities=TB30_ENTITIES, version_string="Thunderbird 30")

# Thunderbird 30 JS changes
TB30_JS_ENTITIES = [
    {"name":"GlodaMsgSearcher.retrievalLimit",
     "status": "removed",
     "bug": 742236,
     "compat_type": "error"},
    {"name":"GlodaIMSearcher.retrievalLimit",
     "status": "removed",
     "bug": 742236,
     "compat_type": "error"},
    {"name":"getNonHtmlRecipients",
     "status": "removed",
     "bug": 970118,
     "compat_type": "error"},
]
register_changed_entities(version_definition=TB30_DEFINITION,
    entities=TB30_JS_ENTITIES, version_string="Thunderbird 30")

# Thunderbird 31 IDL changes
TB31_ENTITIES = [
    {"name":"nsIFolderLookupService.getFolderById",
         "status": "removed",
         "bug": 441437,
         "compat_type": "error"},
    {"name":"nsIAbCard.kAllowRemoteContentProperty",
         "status": "removed",
         "bug": 457296,
         "compat_type": "error"},
    {"name":"nsIAddrDatabase.addAllowRemoteContent",
         "status": "removed",
         "bug": 457296,
         "compat_type": "error"},
]
register_changed_entities(version_definition=TB31_DEFINITION,
    entities=TB31_ENTITIES, version_string="Thunderbird 31")

# Thunderbird 31 JS changes
TB31_JS_ENTITIES = [
    {"name":"ircAccount.kFields.away",
         "status": "removed",
         "bug": 955698,
         "compat_type": "error"},
    {"name":"ircAccount.kFields.idleTime",
         "status": "removed",
         "bug": 987577,
         "compat_type": "error"},
    {"name":"updateCharsetPopupMenu",
         "status": "renamed to EditorUpdateCharsetMenu",
         "bug": 992643,
         "compat_type": "error"},
    {"name":"EditorSetDocumentCharacterSet",
         "status": "renamed to EditorSetCharacterSet",
         "bug": 992643,
         "compat_type": "error"},
    {"name":"EmailConfigWizard.onChangedAuth",
         "status": "renamed to onChangedInAuth",
         "bug": 883670,
         "compat_type": "error"},
    {"name":"EmailConfigWizard.onInputUsername",
         "status": "renamed to onInputOutUsername",
         "bug": 883670,
         "compat_type": "error"},
    {"name":"awArrowHit",
         "status": "removed",
         "bug": 959209,
         "compat_type": "error"},
    {"name":"UpdateMailEditCharset",
         "status": "removed",
         "bug": 999881,
         "compat_type": "error"},
    {"name":"InitCharsetMenuCheckMark",
         "status": "removed",
         "bug": 999881,
         "compat_type": "error"},
    {"name":"gSecurityPane.readAcceptCookies",
         "status": "moved to gPrivacyPane.readAcceptCookies",
         "bug": 953426,
         "compat_type": "error"},
    {"name":"gSecurityPane.writeAcceptCookies",
         "status": "moved to gPrivacyPane.writeAcceptCookies",
         "bug": 953426,
         "compat_type": "error"},
    {"name":"gSecurityPane.showCookieExceptions",
         "status": "moved to gPrivacyPane.showCookieExceptions",
         "bug": 953426,
         "compat_type": "error"},
    {"name":"gSecurityPane.showCookies",
         "status": "moved to gPrivacyPane.showCookies",
         "bug": 953426,
         "compat_type": "error"},
    {"name":"allowRemoteContentForSender",
         "status": "removed",
         "bug": 457296,
         "compat_type": "error"},
    {"name":"allowRemoteContentForSite",
         "status": "renamed to allowRemoteContentForURI",
         "bug": 457296,
         "compat_type": "error"},
    {"name":"createNewHeaderView",
         "status": "renamed to HeaderView",
         "bug": 898860,
         "compat_type": "error"},
    {"name":"FolderDisplayWidget.getVisibleRowPadding",
         "status": "changed",
         "bug": 964824,
         "compat_type": "error"},
]
register_changed_entities(version_definition=TB31_DEFINITION,
    entities=TB31_JS_ENTITIES, version_string="Thunderbird 31")


@register_entity("getShortcutOrURIAndPostData")
def getShortcutOrURIAndPostData(traverser):
    def getShortcutOrURIAndPostData_called(wrapper, arguments, traverser):
        if len(arguments) == 1:
            traverser.warning(
                err_id=("js", "entities", "getShortcutOrURIAndPostData"),
                warning="`getShortcutOrURIAndPostData` no longer returns a "
                        "promise",
                description="getShortcutOrURIAndPostData now takes a "
                            "callback as a second argument, instead of "
                            "returning a Promise. See %s for more "
                            "information." % BUGZILLA_BUG % 989984,
                for_appversions=FX31_DEFINITION,
                compatibility_type="error",
                tier=5)

    return {"return": getShortcutOrURIAndPostData_called}


FX32_ENTITIES = [
    "nsICacheEntryDescriptor",
    "nsICacheListener",
    "nsICacheService",
    "nsICacheSession",
    "nsICacheVisitor",
]
FX32_BLOG = "http://www.janbambas.cz/http-cache-v1-api-disabled/"
FX32_MDN = "https://developer.mozilla.org/docs/HTTP_Cache"

for name in FX32_ENTITIES:
    deprecated_entity(
        name=name,
        version=FX32_DEFINITION,
        message="{name} has been removed. Read more at {blog} and {mdn}."
                .format(name=name, blog=FX32_BLOG, mdn=FX32_MDN),
        bug=999577)
