from call_definitions import open_in_chrome_context
from instanceproperties import _set_HTML_property
from validator.compat import (FX10_DEFINITION, FX14_DEFINITION, FX16_DEFINITION,
                              TB14_DEFINITION, TB15_DEFINITION, TB16_DEFINITION)
from validator.constants import BUGZILLA_BUG


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(function):
        ENTITIES[name] = function
        return function
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
            err_id=("testcases_javascript_entity_values", name),
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


@register_entity("XML")
def XML(traverser):
    return {"dangerous": traverser.warn_e4x}


@register_entity("document.write")
def document_write(traverser):
    def on_write(wrapper, arguments, traverser):
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
                    "be avoided in favor of the HTML5 audio APIs.",
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
