from call_definitions import open_in_chrome_context
from instanceproperties import _set_HTML_property
from validator.compat import TB29_DEFINITION, TB30_DEFINITION, TB31_DEFINITION
from validator.constants import BUGZILLA_BUG


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(func):
        ENTITIES[name] = func
        return func
    return wrap


def entity(name, result=None):
    assert name in ENTITIES

    def return_wrap(t):
        output = ENTITIES[name](traverser=t)
        if result is not None:
            return result
        elif output is not None:
            return output
        else:
            return {'value': {}}
    return {'value': return_wrap}


def deprecated_entity(name, version, message, bug, status='deprecated',
                      compat_type='error'):
    def wrap(traverser):
        traverser.err.warning(
            err_id=('js', 'entities', name),
            warning='`%s` has been %s.' % (name, status),
            description=(message,
                         'See %s for more information.' % BUGZILLA_BUG % bug),
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
            name=entity['name'],
            version=version_definition,
            message='The method or property `%s` has been `%s` in `%s`.'
                % (entity['name'], entity['status'], version_string),
            bug=entity['bug'],
            compat_type=entity['compat_type'])


DOC_WRITE_MSG = ('https://developer.mozilla.org/docs/XUL/School_tutorial/'
                 'DOM_Building_and_HTML_Insertion')

@register_entity('document.write')
def document_write(traverser):
    def on_write(wrapper, arguments, traverser):
        traverser.err.warning(
            err_id=('js', 'document.write', 'evil'),
            warning='Use of `document.write` strongly discouraged.',
            description=('`document.write` will fail in many circumstances ',
                         'when used in extensions, and has potentially severe '
                         'security repercussions when used improperly. '
                         'Therefore, it should not be used. See %s for more '
                         'information.' % DOC_WRITE_MSG),
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)
        if not arguments:
            return
        value = traverser._traverse_node(arguments[0])
        _set_HTML_property('document.write()', value, traverser)

    return {'return': on_write}


@register_entity('nsIDNSService.resolve')
def nsIDNSServiceResolve(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsIDNSServiceResolve'),
        warning='`nsIDNSService.resolve()` should not be used.',
        description='The `nsIDNSService.resolve` method performs a '
                    'synchronous DNS lookup, which will freeze the UI. This '
                    'can result in severe performance issues. '
                    '`nsIDNSService.asyncResolve()` should be used instead.',
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity('nsISound.play')
def nsISoundPlay(traverser):
    traverser.err.warning(
        err_id=('testcases_javascript_entity_values',
                'nsISound_play'),
        warning='`nsISound.play` should not be used.',
        description='The `nsISound.play` function is synchronous, and thus '
                    'freezes the interface while the sound is playing. It '
                    'should be avoided in favor of the HTML5 audio APIs.',
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


@register_entity('nsIWindowWatcher.openWindow')
def nsIWindowWatcher_openWindow(traverser):
    def on_open(wrapper, arguments, traverser):
        if not arguments:
            return
        uri = traverser._traverse_node(arguments[0])
        open_in_chrome_context(uri, 'nsIWindowWatcher.openWindow', traverser)

    return {'return': on_open}


@register_entity('nsITransferable.init')
def nsITransferable_init(traverser):
    def on_init(wrapper, arguments, traverser):
        if not arguments:
            return
        first_arg = traverser._traverse_node(arguments[0])
        if first_arg.get_literal_value():
            return
        traverser.err.warning(
            err_id=('js_entity_values', 'nsITransferable', 'init'),
            warning='`init` should not be called with a null first argument',
            description='Calling `nsITransferable.init()` with a null first '
                        'argument has the potential to leak data across '
                        'private browsing mode sessions. `null` is  '
                        'appropriate only when reading data or writing data '
                        'which is not associated with a particular window.',
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)

    return {'return': on_init}


@register_entity('NewTabURL.override')
def NewTabURL_override(traverser):
    def on_override(wrapper, arguments, traverser):
        # Import loop.
        from validator.testcases.javascript.predefinedentities import (
            CUSTOMIZATION_API_HELP)
        traverser.err.warning(
            err_id=('js_entity_values', 'NewTabURL', 'override'),
            warning='Extensions must not alter user preferences such as the '
                    'new tab URL without explicit user consent.',
            description='Extensions must not alter user preferences such as '
                        'the new tab URL without explicit user consent. Such '
                        'changes must also be reverted when the extension is '
                        'disabled or uninstalled.',
            signing_severity='high',
            signing_help='Add-ons which directly change these preferences must '
                         'undergo manual code review for at least one '
                         'submission. ' + CUSTOMIZATION_API_HELP,
        )
    return {'return': on_override}


# Thunderbird 29 JS changes
TB29_JS_ENTITIES = [
    {'name':'DisablePhishingWarning',
     'status': '',
     'bug': 926473,
     'compat_type': 'error'},
    {'name':'RoomInfo',
     'status': '',
     'bug': 920801,
     'compat_type': 'error'},
    {'name':'FillInHTMLTooltip',
     'status': '',
     'bug': 956586,
     'compat_type': 'error'},
    {'name':'escapeXMLchars',
     'status': '',
     'bug': 942638,
     'compat_type': 'error'},
    {'name':'gPluginHandler.isTooSmall',
     'status': 'removed',
     'bug': 951800,
     'compat_type': 'error'},
    {'name':'XMPPSession.authDialog',
     'status': 'removed',
     'bug': 920801,
     'compat_type': 'error'},
    {'name':'XMPPMUCConversation.supportChatStateNotifications',
     'status': 'removed',
     'bug': 920801,
     'compat_type': 'error'},
    {'name':'Socket.inputSegmentSize',
     'status': 'removed',
     'bug': 920801,
     'compat_type': 'error'},
    {'name':'XMPPMUCConversationPrototype.normalizedName',
     'status': 'removed',
     'bug': 957918,
     'compat_type': 'error'},
    {'name':'XMPPAccountBuddyPrototype.normalizedName',
     'status': 'removed',
     'bug': 957918,
     'compat_type': 'error'},
    {'name':'XMPPAccountPrototype.normalizedName',
     'status': 'removed',
     'bug': 957918,
     'compat_type': 'error'},
    {'name':'GenericAccountPrototype.maxMessageLength',
     'status': 'removed',
     'bug': 954484,
     'compat_type': 'error'},
    {'name':'mailTabType.desiredColumnStates',
     'status': 'removed',
     'bug': 528044,
     'compat_type': 'error'},
]
register_changed_entities(version_definition=TB29_DEFINITION,
    entities=TB29_JS_ENTITIES, version_string='Thunderbird 29')

# Thunderbird 30 IDL changes
TB30_ENTITIES = [
    {'name':'nsIMsgDatabase.forceFolderDBClosed',
     'status': 'moved to nsIMsgDBService',
     'bug': 876548,
     'compat_type': 'error'},
    {'name':'nsIMsgCompose.checkAndPopulateRecipients',
     'status': 'removed',
     'bug': 970118,
     'compat_type': 'error'},
]
register_changed_entities(version_definition=TB30_DEFINITION,
    entities=TB30_ENTITIES, version_string='Thunderbird 30')

# Thunderbird 30 JS changes
TB30_JS_ENTITIES = [
    {'name':'GlodaMsgSearcher.retrievalLimit',
     'status': 'removed',
     'bug': 742236,
     'compat_type': 'error'},
    {'name':'GlodaIMSearcher.retrievalLimit',
     'status': 'removed',
     'bug': 742236,
     'compat_type': 'error'},
    {'name':'getNonHtmlRecipients',
     'status': 'removed',
     'bug': 970118,
     'compat_type': 'error'},
]
register_changed_entities(version_definition=TB30_DEFINITION,
    entities=TB30_JS_ENTITIES, version_string='Thunderbird 30')

# Thunderbird 31 IDL changes
TB31_ENTITIES = [
    {'name':'nsIFolderLookupService.getFolderById',
         'status': 'removed',
         'bug': 441437,
         'compat_type': 'error'},
    {'name':'nsIAbCard.kAllowRemoteContentProperty',
         'status': 'removed',
         'bug': 457296,
         'compat_type': 'error'},
    {'name':'nsIAddrDatabase.addAllowRemoteContent',
         'status': 'removed',
         'bug': 457296,
         'compat_type': 'error'},
]
register_changed_entities(version_definition=TB31_DEFINITION,
    entities=TB31_ENTITIES, version_string='Thunderbird 31')

# Thunderbird 31 JS changes
TB31_JS_ENTITIES = [
    {'name':'ircAccount.kFields.away',
         'status': 'removed',
         'bug': 955698,
         'compat_type': 'error'},
    {'name':'ircAccount.kFields.idleTime',
         'status': 'removed',
         'bug': 987577,
         'compat_type': 'error'},
    {'name':'updateCharsetPopupMenu',
         'status': 'renamed to EditorUpdateCharsetMenu',
         'bug': 992643,
         'compat_type': 'error'},
    {'name':'EditorSetDocumentCharacterSet',
         'status': 'renamed to EditorSetCharacterSet',
         'bug': 992643,
         'compat_type': 'error'},
    {'name':'EmailConfigWizard.onChangedAuth',
         'status': 'renamed to onChangedInAuth',
         'bug': 883670,
         'compat_type': 'error'},
    {'name':'EmailConfigWizard.onInputUsername',
         'status': 'renamed to onInputOutUsername',
         'bug': 883670,
         'compat_type': 'error'},
    {'name':'awArrowHit',
         'status': 'removed',
         'bug': 959209,
         'compat_type': 'error'},
    {'name':'UpdateMailEditCharset',
         'status': 'removed',
         'bug': 999881,
         'compat_type': 'error'},
    {'name':'InitCharsetMenuCheckMark',
         'status': 'removed',
         'bug': 999881,
         'compat_type': 'error'},
    {'name':'gSecurityPane.readAcceptCookies',
         'status': 'moved to gPrivacyPane.readAcceptCookies',
         'bug': 953426,
         'compat_type': 'error'},
    {'name':'gSecurityPane.writeAcceptCookies',
         'status': 'moved to gPrivacyPane.writeAcceptCookies',
         'bug': 953426,
         'compat_type': 'error'},
    {'name':'gSecurityPane.showCookieExceptions',
         'status': 'moved to gPrivacyPane.showCookieExceptions',
         'bug': 953426,
         'compat_type': 'error'},
    {'name':'gSecurityPane.showCookies',
         'status': 'moved to gPrivacyPane.showCookies',
         'bug': 953426,
         'compat_type': 'error'},
    {'name':'allowRemoteContentForSender',
         'status': 'removed',
         'bug': 457296,
         'compat_type': 'error'},
    {'name':'allowRemoteContentForSite',
         'status': 'renamed to allowRemoteContentForURI',
         'bug': 457296,
         'compat_type': 'error'},
    {'name':'createNewHeaderView',
         'status': 'renamed to HeaderView',
         'bug': 898860,
         'compat_type': 'error'},
    {'name':'FolderDisplayWidget.getVisibleRowPadding',
         'status': 'changed',
         'bug': 964824,
         'compat_type': 'error'},
]
register_changed_entities(version_definition=TB31_DEFINITION,
    entities=TB31_JS_ENTITIES, version_string='Thunderbird 31')
