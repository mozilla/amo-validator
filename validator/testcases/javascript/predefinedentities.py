from functools import partial
import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import xpcom_constructor as xpcom_const, python_wrap
from entity_values import entity
import instanceactions
from jstypes import JSWrapper
from validator.compat import FX40_DEFINITION
from validator.constants import MDN_DOC


# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = {
    u'newThread':
        'Creating threads from JavaScript is a common cause '
        'of crashes and is unsupported in recent versions of the platform',
    u'processNextEvent':
        'Spinning the event loop with processNextEvent is a common cause of '
        'deadlocks, crashes, and other errors due to unintended reentrancy. '
        'Please use asynchronous callbacks instead wherever possible',
}

CUSTOMIZATION_API_HELP = (
    'We are currently working to provide libraries and APIs to allow '
    'extensions to modify these settings in ways that we can guarantee are '
    'in-policy. In the interim, we recommend that you avoid changing these '
    'settings altogether, if at all possible.')

CUSTOMIZATION_PREF_MESSAGE = {
    'description': (
        'Extensions must not alter user preferences such as the current home '
        'page, new tab page, or search engine, without explicit user consent, '
        'in which a user takes a non-default action. Such changes must also '
        'be reverted when the extension is disabled or uninstalled.',
        'In nearly all cases, new values for these preferences should be '
        'set in the default preference branch, rather than the user branch.'),
    'signing_help':
        'Add-ons which directly change these preferences must undergo at '
        'manual code review for at least one submission. ' +
        CUSTOMIZATION_API_HELP,
    'signing_severity': 'high',
}

NETWORK_PREF_MESSAGE = {
    'description':
        'Changing network preferences may be dangerous, and often leads to '
        'performance costs.',
    'signing_help':
        'Changes to these preferences are strongly discouraged. If at all '
        'possible, you should remove any reference to them from '
        'your extension. Extensions which do modify these preferences '
        'must undergo light manual code review for at least one submission.',
    'signing_severity': 'low',
}

SEARCH_PREF_MESSAGE = {
    'description':
        'Search engine preferences may not be changed by add-ons directly. '
        'All such changes must be made only via the browser search service, '
        'and only after an explicit opt-in from the user. All such changes '
        'must be reverted when the extension is disabled or uninstalled.',
    'signing_help': (
        'You should remove all references to these preferences from your '
        'code, and interact with search settings only via the '
        '`Services.search` interface. Extensions which interact with these '
        'preferences directly are not acceptable within the Firefox add-on '
        'ecosystem.',
        'Note, however, that extensions which change search settings even via '
        'the search service must undergo manual code review for at least '
        'one submission. ' + CUSTOMIZATION_API_HELP),
    'signing_severity': 'high',
}

SECURITY_PREF_MESSAGE = {
    'description':
        'Changing this preference may have severe security implications, and '
        'is forbidden under most circumstances.',
    'editors_only': True,
    'signing_help': ('Extensions which alter these settings are allowed '
                     'within the Firefox add-on ecosystem by exception '
                     'only, and under extremely limited circumstances.',
                     'Please remove any reference to these preference names '
                     'from your add-on.'),
    'signing_severity': 'high',
}

MARIONETTE_MESSAGE = {
    'warning': 'Marionette should not be accessed by extensions',
    'description': 'References to the Marionette service are not acceptable '
                   'in extensions. Please remove them.',
}


def fuel_error(traverse_node, err):
    traverse_node.im_self.warning(
        err_id=('js', 'traverser', 'dangerous_global'),
        warning='The FUEL library is now deprecated.',
        description='The FUEL library is now deprecated. You should use the '
                    'add-ons SDK or Services.jsm. See %s for more information.'
                    % MDN_DOC % 'Mozilla/Tech/Toolkit_API/FUEL',
        for_appversions=FX40_DEFINITION,
        tier=5,
        compatibility_type='warning')


BANNED_PREF_BRANCHES = (
    # Security and update preferences
    (u'app.update.', SECURITY_PREF_MESSAGE),
    (u'browser.addon-watch.', SECURITY_PREF_MESSAGE),
    (u'capability.policy.', None),
    (u'datareporting.', SECURITY_PREF_MESSAGE),

    (u'extensions.blocklist.', SECURITY_PREF_MESSAGE),
    (u'extensions.checkCompatibility', None),
    (u'extensions.getAddons.', SECURITY_PREF_MESSAGE),
    (u'extensions.update.', SECURITY_PREF_MESSAGE),

    # Let's see if we can get away with this...
    # Changing any preference in this branch should result in a
    # warning. However, this substring may turn out to be too
    # generic, and lead to spurious warnings, in which case we'll
    # have to single out sub-branches.
    (u'security.', SECURITY_PREF_MESSAGE),

    # Search, homepage, and customization preferences
    (u'browser.newtab.url', CUSTOMIZATION_PREF_MESSAGE),
    (u'browser.newtabpage.enabled', CUSTOMIZATION_PREF_MESSAGE),
    (u'browser.search.defaultenginename', SEARCH_PREF_MESSAGE),
    (u'browser.search.searchEnginesURL', SEARCH_PREF_MESSAGE),
    (u'browser.startup.homepage', CUSTOMIZATION_PREF_MESSAGE),
    (u'extensions.getMoreThemesURL', None),
    (u'keyword.URL', SEARCH_PREF_MESSAGE),
    (u'keyword.enabled', SEARCH_PREF_MESSAGE),

    # Network
    (u'network.proxy.autoconfig_url', {
        'description':
            'As many add-ons have reason to change the proxy autoconfig URL, '
            'and only one at a time may do so without conflict, extensions '
            'must make proxy changes using other mechanisms. Installing a '
            'proxy filter is the recommended alternative: '
            'https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XPCOM/'
            'Reference/Interface/nsIProtocolProxyService#registerFilter()',
        'signing_help':
            'Dynamic proxy configuration should be implemented via proxy '
            'filters, as described above. This preference should not be '
            'set, except directly by end users.',
        'signing_severity': 'low'}),
    (u'network.proxy.', NETWORK_PREF_MESSAGE),
    (u'network.http.', NETWORK_PREF_MESSAGE),
    (u'network.websocket.', NETWORK_PREF_MESSAGE),

    # Other
    (u'browser.preferences.instantApply', None),

    (u'extensions.alwaysUnpack', None),
    (u'extensions.bootstrappedAddons', None),
    (u'extensions.dss.', None),
    (u'extensions.installCache', None),
    (u'extensions.lastAppVersion', None),
    (u'extensions.pendingOperations', None),

    (u'general.useragent.', None),

    (u'nglayout.debug.disable_xul_cache', None),

    # Marionette
    (u'marionette.force-local', MARIONETTE_MESSAGE),
    (u'marionette.defaultPrefs.enabled', MARIONETTE_MESSAGE),
    (u'marionette.defaultPrefs.port', MARIONETTE_MESSAGE),
)

BANNED_PREF_REGEXPS = [
    r'extensions\..*\.update\.(url|enabled|interval)',
]


def is_shared_scope(traverser, right=None, node_right=None):
    """Returns true if the traverser `t` is traversing code loaded into
    a shared scope, such as a browser window. Particularly used for
    detecting when global overwrite warnings should be issued."""

    # FIXME(Kris): This is not a great heuristic.
    return not (traverser.is_jsm or
                traverser.err.get_resource('em:bootstrap') == 'true')


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

CONTENT_DOCUMENT = None


CATEGORY_MANAGER = {
    u'addCategoryEntry':
        {'dangerous':
            lambda a, t, e:
                e.get_resource('em:bootstrap') and
                ('Bootstrapped add-ons may not create persistent category '
                 'entries.' if len(a) > 3 and t(a[3]).is_literal() else
                 'Authors of bootstrapped add-ons must take care to clean up '
                 'any added category entries at shutdown.')}}


OBSOLETE_EXTENSION_MANAGER = {
    'value': {},
    'dangerous': 'This interface is part of the obsolete extension manager '
                 'interface, which is not available in any remotely modern '
                 'version of Firefox. It should not be referenced in any '
                 'code.'}


ADDON_INSTALL_METHOD = {
    'value': {},
    'dangerous': {
        'description': (
            'Add-ons may install other add-ons only by user consent. Any '
            'such installations must be carefully reviewed to ensure '
            'their safety.'),
        'editors_only': True,
        'signing_help': (
            'Rather than directly install other add-ons, you should offer '
            'users the opportunity to install them via the normal web install '
            'process, using an install link or button connected to the '
            '`InstallTrigger` API: '
            'https://developer.mozilla.org/en-US/docs/Web/API/InstallTrigger',
            'Updates to existing add-ons should be provided via the '
            'install.rdf `updateURL` mechanism.'),
        'signing_severity': 'high'},
}


SEARCH_MESSAGE = 'Potentially dangerous use of the search service'
SEARCH_DESCRIPTION = (
    'Changes to the default and currently-selected search engine settings '
    'may only take place after users have explicitly opted-in, by taking '
    'a non-default action. Any such changes must be reverted when the add-on '
    'making them is disabled or uninstalled.')

def search_warning(severity='medium', editors_only=False,
                   message=SEARCH_MESSAGE,
                   description=SEARCH_DESCRIPTION):
    return {'err_id': ('testcases_javascript_actions',
                       'search_service',
                       'changes'),
            'signing_help':
                'Add-ons which directly change search settings must undergo '
                'manual code review for at least one submission. ' +
                CUSTOMIZATION_API_HELP,
            'signing_severity': severity,
            'editors_only': editors_only,
            'warning': message,
            'description': description}


REGISTRY_WRITE = {'dangerous': {
    'err_id': ('testcases_javascript_actions',
               'windows_registry',
               'write'),
    'warning': 'Writes to the registry may be dangerous',
    'description': 'Writing to the registry can have many system-level '
                   'consequences and requires careful review.',
    'signing_help': (
        'Please store any settings relevant to your add-on within the '
        'current Firefox profile, ideally using the preferences service.'
        'If you are intentionally changing system settings, consider '
        'searching for a Firefox API which has a similar effect. If no such '
        'API exists, we strongly discourage making any changes which affect '
        'the system outside of the browser.'),
    'signing_severity': 'medium',
    'editors_only': True}}


def registry_key(write=False):
    """Represents a function which returns a registry key object."""
    res = {'return': lambda wrapper, arguments, traverser: (
        build_quick_xpcom('createInstance', 'nsIWindowMediator',
                          traverser, wrapper=True))}
    if write:
        res.update(REGISTRY_WRITE)

    return res


INTERFACES = {
    u'nsISupports': {'value': {}},
    u'mozIStorageBaseStatement':
        {'value':
            {u'execute':
                {'dangerous': instanceactions.SYNCHRONOUS_SQL_DESCRIPTION},
             u'executeStep':
                {'dangerous': instanceactions.SYNCHRONOUS_SQL_DESCRIPTION}}},
    u'nsIExtensionManager': OBSOLETE_EXTENSION_MANAGER,
    u'nsIUpdateItem': OBSOLETE_EXTENSION_MANAGER,
    u'nsIInstallLocation': OBSOLETE_EXTENSION_MANAGER,
    u'nsIAddonInstallListener': OBSOLETE_EXTENSION_MANAGER,
    u'nsIAddonUpdateCheckListener': OBSOLETE_EXTENSION_MANAGER,
    u'nsICategoryManager':
        {'value': CATEGORY_MANAGER},
    u'nsIAccessibleRetrieval':
        {'dangerous':
            'Using the nsIAccessibleRetrieval interface causes significant '
            'performance degradation in Gecko. It should only be used in '
            'accessibility-related add-ons.',
         'value': {}},
    u'nsIBrowserSearchService':
        {'value':
            {u'currentEngine':
                {'readonly': search_warning(severity='high')},
             u'defaultEngine':
                {'readonly': search_warning(severity='high')},
             u'addEngine':
                {'dangerous': search_warning()},
             u'addEngineWithDetails':
                {'dangerous': search_warning()},
             u'removeEngine':
                {'dangerous': search_warning()},
             u'moveEngine':
                {'dangerous': search_warning()}}},

    u'nsIComponentRegistrar':
        {'value':
            {u'autoRegister':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Bootstrapped add-ons may not register chrome '
                        'manifest files.'},
             u'registerFactory':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care to '
                        'clean up any component registrations at shutdown.'}}},
    u'nsIDNSService': {'value': {u'resolve': entity('nsIDNSService.resolve')}},
    u'nsIJSON':
        {'value':
            {u'encode':
                {'return': call_definitions.nsIJSON_deprec},
             u'decode':
                {'return': call_definitions.nsIJSON_deprec}}},
    u'nsIMsgDatabase':
        {'value':
            {u'forceFolderDBClosed': entity('nsIMsgDatabase.forceFolderDBClosed')}},
    u'nsIObserverService':
        {'value':
            {u'addObserver':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care '
                        'to remove any added observers '
                        'at shutdown.'}},
         'dangerous': lambda a, t, e:
            lambda t, e: (
                e.metadata.get('is_jetpack') and
                'The observer service should not be used directly in SDK '
                "add-ons. Please use the 'sdk/system/events' module "
                'instead.')},
    u'nsIPrefBranch':
        {'value': dict(
            tuple((method, {'return': instanceactions.set_preference})
                   for method in (u'setBoolPref',
                                  u'setCharPref',
                                  u'setComplexValue',
                                  u'setIntPref',
                                  u'clearUserPref',
                                  u'deleteBranch',
                                  u'resetBranch')) +
            tuple((method, {'return': instanceactions.get_preference})
                   for method in (u'getBoolPref',
                                  u'getCharPref',
                                  u'getChildList',
                                  u'getComplexValue',
                                  u'getFloatPref',
                                  u'getIntPref',
                                  u'getPrefType',
                                  u'prefHasUserValue')))},
    u'nsIResProtocolHandler':
        {'value':
            {u'setSubstitution':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        a and len(a) > 1 and t(a[1]).get_literal_value() and
                        'Authors of bootstrapped add-ons must take care '
                        'to clean up any added resource substitutions '
                        'at shutdown.'}}},
    u'nsISound': {'value': {'play': entity('nsISound.play')}},
    u'nsIStringBundleService':
        {'value':
            {u'createStringBundle':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care '
                        'to flush the string bundle cache at shutdown.'},
             u'createExtensibleBundle':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care '
                        'to flush the string bundle cache at shutdown.'}}},
    u'nsIStyleSheetService':
        {'value':
            {u'loadAndRegisterSheet':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care to '
                        'unregister registered stylesheets at shutdown.'}}},
    u'nsITransferable':
        {'value':
            {u'init':
                entity('nsITransferable.init')}},
    u'nsIWindowMediator':
        {'value':
            {'registerNotification':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care '
                        'to remove any added observers at shutdown.'}}},
    u'nsIWindowWatcher':
        {'value':
            {u'addListener':
                {'dangerous':
                    lambda a, t, e:
                        e.get_resource('em:bootstrap') and
                        'Authors of bootstrapped add-ons must take care '
                        'to remove any added observers at shutdown.'},
             u'openWindow': entity('nsIWindowWatcher.openWindow')}},
    u'nsIProtocolProxyService': {'value': {
        u'registerFilter': {'dangerous': {
            'err_id': ('testcases_javascript_actions',
                       'predefinedentities', 'proxy_filter'),
            'description': (
                'Proxy filters can be used to direct arbitrary network '
                'traffic through remote servers, and may potentially '
                'be abused.',
                'Additionally, to prevent conflicts, the `applyFilter` '
                'method should always return its third argument in cases '
                'when it is not supplying a specific proxy.'),
            'editors_only': True,
            'signing_help': 'Due to the potential for unintended effects, '
                            'any add-on which uses this API must undergo '
                            'manual code review for at least one submission.',
            'signing_severity': 'low'}}}},
    u'nsIWebBrowserPersist':
        {'value':
             {u'saveChannel':
                  {'return': call_definitions.webbrowserpersist},
              u'saveURI':
                  {'return':
                       call_definitions.webbrowserpersist_saveuri},
              u'savePrivacyAwareURI':
                  {'return': call_definitions.webbrowserpersist}}},
    u'nsIMsgCompose':
        {'value':
             {u'checkAndPopulateRecipients': entity('nsIMsgCompose.checkAndPopulateRecipients')}},
    u'nsIFolderLookupService':
        {'value':
             {u'getFolderById': entity('nsIFolderLookupService.getFolderById')}},
    u'nsIAbCard':
        {'value':
             {u'kAllowRemoteContentProperty': entity('nsIAbCard.kAllowRemoteContentProperty')}},
    u'nsIAddrDatabase':
        {'value':
             {u'addAllowRemoteContent': entity('nsIAddrDatabase.addAllowRemoteContent')}},

    'nsIWindowsRegKey': {'value': {u'create': REGISTRY_WRITE,
                                   u'createChild': registry_key(write=True),
                                   u'openChild': registry_key(),
                                   u'writeBinaryValue': REGISTRY_WRITE,
                                   u'writeInt64Value': REGISTRY_WRITE,
                                   u'writeIntValue': REGISTRY_WRITE,
                                   u'writeStringValue': REGISTRY_WRITE,
                                  }},
    }

INTERFACE_ENTITIES = {u'nsIXMLHttpRequest':
                          {'xpcom_map':
                               lambda: GLOBAL_ENTITIES['XMLHttpRequest']},
                      u'nsIProcess': {'dangerous': {
                        'warning': 'The use of nsIProcess is potentially '
                                   'dangerous and requires careful review '
                                   'by an administrative reviewer.',
                        'editors_only': True,
                        'signing_help':
                          'Consider alternatives to directly launching '
                          'executables, such as loading a URL with an '
                          'appropriate external protocol handler, making '
                          'network requests to a local service, or using '
                          'the (as a last resort) `nsIFile.launch()` method '
                          'to open a file with the appropriate application.',
                        'signing_severity': 'high',
                      }},
                      u'nsIDOMGeoGeolocation': {'dangerous':
                         'Use of the geolocation API by add-ons requires '
                         'prompting users for consent.'},
                      u'nsIWindowsRegKey': {'dangerous': {
                          'signing_help':
                            'The information stored in many standard registry '
                            'keys is available via built-in Firefox APIs, '
                            'such as `Services.sysinfo`, `Services.dirsvc`, '
                            'and the environment service '
                            '(http://mzl.la/1OGgCF3). We strongly discourage '
                            'extensions from reading registry information '
                            'which is not available via other Firefox APIs.',
                          'signing_severity': 'low',
                          'editors_only': True,
                          'description': (
                              'Access to the registry is potentially '
                              'dangerous, and should be reviewed with special '
                              'care.')}},
                      }

DANGEROUS_CERT_DB = {
    'err_id': ('javascript', 'predefinedentities', 'cert_db'),
    'description': 'Access to the X509 certificate '
                   'database is potentially dangerous '
                   'and requires careful review by an '
                   'administrative reviewer.',
    'editors_only': True,
    'signing_help': 'Please avoid interacting with the certificate and trust '
                    'databases if at all possible. Any add-ons which interact '
                    'with these databases must undergo manual code review '
                    'prior to signing.',
    'signing_severity': 'high',
}

INTERFACE_ENTITIES.update(
    (interface, {'dangerous': DANGEROUS_CERT_DB})
    for interface in ('nsIX509CertDB', 'nsIX509CertDB2', 'nsIX509CertList',
                      'nsICertOverrideService'))

CONTRACT_ENTITIES = {
    contract: DANGEROUS_CERT_DB
    for contract in ('@mozilla.org/security/x509certdb;1',
                     '@mozilla.org/security/x509certlist;1',
                     '@mozilla.org/security/certoverride;1')}

for interface in INTERFACES:
    def construct(interface):
        def wrap():
            return INTERFACES[interface]
        return wrap
    if interface not in INTERFACE_ENTITIES:
        INTERFACE_ENTITIES[interface] = {}
    INTERFACE_ENTITIES[interface]['xpcom_map'] = construct(interface)


def build_quick_xpcom(method, interface, traverser, wrapper=False):
    """A shortcut to quickly build XPCOM objects on the fly."""
    extra = ()
    if isinstance(interface, (list, tuple)):
        interface, extra = interface[0], interface[1:]

    def interface_obj(iface):
        return traverser._build_global(
            name=method,
            entity={'xpcom_map':
                lambda: INTERFACES.get(iface, INTERFACES['nsISupports'])})

    constructor = xpcom_const(method, pretraversed=True)
    obj = constructor(None, [interface_obj(interface)], traverser)

    for iface in extra:
        # `xpcom_constructor` really needs to be cleaned up so we can avoid
        # this duplication.
        iface = interface_obj(iface)
        iface = traverser._build_global('QueryInterface',
                                        iface.value['xpcom_map']())

        obj.value = obj.value.copy()

        value = obj.value['value'].copy()
        value.update(iface.value['value'])

        obj.value.update(iface.value)
        obj.value['value'] = value

    if isinstance(obj, JSWrapper) and not wrapper:
        obj = obj.value
    return obj


UNSAFE_TEMPLATE_METHOD = (
    'The use of `%s` can lead to unsafe '
    'remote code execution, and therefore must be done with '
    'great care, and only with sanitized data.')


SERVICES = {
    'appinfo': ('nsIXULAppInfo', 'nsIXULRuntime'),
    'appShell': 'nsIAppShellService',
    'blocklist': 'nsIBlocklistService',
    'cache': 'nsICacheService',
    'cache2': 'nsICacheStorageService',
    'clipboard': 'nsIClipboard',
    'console': 'nsIConsoleService',
    'contentPrefs': 'nsIContentPrefService',
    'cookies': ('nsICookieManager', 'nsICookieManager2', 'nsICookieService'),
    'dirsvc': ('nsIDirectoryService', 'nsIProperties'),
    'DOMRequest': 'nsIDOMRequestService',
    'domStorageManager': 'nsIDOMStorageManager',
    'downloads': 'nsIDownloadManager',
    'droppedLinkHandler': 'nsIDroppedLinkHandler',
    'eTLD': 'nsIEffectiveTLDService',
    'focus': 'nsIFocusManager',
    'io': ('nsIIOService', 'nsIIOService2'),
    'locale': 'nsILocaleService',
    'logins': 'nsILoginManager',
    'obs': 'nsIObserverService',
    'perms': 'nsIPermissionManager',
    'prefs': ('nsIPrefBranch2', 'nsIPrefService', 'nsIPrefBranch'),
    'prompt': 'nsIPromptService',
    'scriptloader': 'mozIJSSubScriptLoader',
    'scriptSecurityManager': 'nsIScriptSecurityManager',
    'search': 'nsIBrowserSearchService',
    'startup': 'nsIAppStartup',
    'storage': 'mozIStorageService',
    'strings': 'nsIStringBundleService',
    'sysinfo': 'nsIPropertyBag2',
    'telemetry': 'nsITelemetry',
    'tm': 'nsIThreadManager',
    'uriFixup': 'nsIURIFixup',
    'urlFormatter': 'nsIURLFormatter',
    'vc': 'nsIVersionComparator',
    'wm': 'nsIWindowMediator',
    'ww': 'nsIWindowWatcher',
}

for key, value in SERVICES.items():
    SERVICES[key] = {'value': partial(build_quick_xpcom,
                                      'getService', value)}

DANGEROUS_EVAL = {
    'err_id': ('javascript', 'dangerous_global', 'eval'),
    'description': ('Evaluation of strings as code can lead to security '
                    'vulnerabilities and performance issues, even in the '
                    'most innocuous of circumstances. Please avoid using '
                    '`eval` and the `Function` constructor when at all '
                    'possible.',
                    'Alternatives are available for most use cases. See '
                    'https://developer.mozilla.org/en-US/Add-ons/'
                    'Overlay_Extensions/XUL_School/'
                    'Appendix_C:_Avoid_using_eval_in_Add-ons '
                    'for more information.'),
    'signing_help':
        'Please try to avoid evaluating strings as code wherever possible. '
        'Read over the linked document for suggested alternatives. '
        'If you are referencing the `Function` constructor without calling '
        'it, and cannot avoid continuing to do so, consider alternatives '
        'such as calling `Object.getPrototypeOf` on an existing function '
        'object.',
    'signing_severity': 'high'}

FUNCTION_EXPORT_HELP = (
    'Given the potential security risks of exposing APIs to unprivileged '
    'code, extensions which use these APIs must undergo manual review for at '
    'least one submission. If you are not using these APIs to interact with '
    'content code, please consider alternatives, such as built-in '
    'message passing functionality.')

# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u'window': {'value': lambda t: {'value': GLOBAL_ENTITIES}},
    u'null': {'literal': lambda t: JSWrapper(None, traverser=t)},
    u'Cc': {'readonly': False,
            'value':
                lambda t: GLOBAL_ENTITIES['Components']['value']['classes']},
    u'Ci': {'readonly': False,
            'value':
                lambda t: GLOBAL_ENTITIES['Components']['value']['interfaces']},
    u'Cu': {'readonly': False,
            'value':
                lambda t: GLOBAL_ENTITIES['Components']['value']['utils']},

    # From Services.jsm.
    u'Services': {'value': SERVICES},

    # From Preferences.jsm.
    # TODO: Support calls that return instances of this object which
    # operate on non-root branches.
    u'Preferences': {'value': {
        u'get': {'return': instanceactions.get_preference},
        u'reset': {'return': instanceactions.set_preference},
        u'resetBranch': {'return': instanceactions.set_preference},
        u'set': {'return': instanceactions.set_preference}}},

    u'AddonManager': {
        'readonly': False,
        'value': {
            u'autoUpdateDefault': {'readonly': SECURITY_PREF_MESSAGE},
            u'checkUpdateSecurity': {'readonly': SECURITY_PREF_MESSAGE},
            u'checkUpdateSecurityDefault': {'readonly': SECURITY_PREF_MESSAGE},
            u'updateEnabled': {'readonly': SECURITY_PREF_MESSAGE},
            u'getInstallForFile': ADDON_INSTALL_METHOD,
            u'getInstallForURL': ADDON_INSTALL_METHOD,
            u'installAddonsFromWebpage': ADDON_INSTALL_METHOD}},

    u'ctypes': {'dangerous': {
        'description': (
            'Insufficiently meticulous use of ctypes can lead to serious, '
            'and often exploitable, errors. The use of bundled binary code, '
            'or access to system libraries, may allow for add-ons to '
            'perform unsafe operations. All ctypes use must be carefully '
            'reviewed by a qualified reviewer.'),
        'editors_only': True,
        'signing_help': ('Please try to avoid interacting with or bundling '
                         'native binaries whenever possible. If you are '
                         'bundling binaries for performance reasons, please '
                         'consider alternatives such as Emscripten '
                         '(http://mzl.la/1KrSUh2), JavaScript typed arrays '
                         '(http://mzl.la/1Iw02sr), and Worker threads '
                         '(http://mzl.la/1OGfAcc).',
                         'Any code which makes use of the `ctypes` API '
                         'must undergo manual code review for at least one '
                         'submission.'),
        'signing_severity': 'high'}},

    u'document':
        {'value':
             {u'title':
                  {'overwriteable': True,
                   'readonly': False},
              u'defaultView':
                  {'value': lambda t: {'value': GLOBAL_ENTITIES}},
              u'loadOverlay':
                  {'dangerous':
                       lambda a, t, e:
                           not a or not _get_as_str(t(a[0])).lower()
                               .startswith(('chrome:', 'resource:'))},
              u'write': entity('document.write'),
              u'writeln': entity('document.write')}},

    # The nefariuos timeout brothers!
    u'setTimeout': {'dangerous': actions._call_settimeout},
    u'setInterval': {'dangerous': actions._call_settimeout},

    u'require': {'dangerous': actions._call_require},

    u'encodeURI': {'readonly': True},
    u'decodeURI': {'readonly': True},
    u'encodeURIComponent': {'readonly': True},
    u'decodeURIComponent': {'readonly': True},
    u'escape': {'readonly': True},
    u'unescape': {'readonly': True},
    u'isFinite': {'readonly': True},
    u'isNaN': {'readonly': True},
    u'parseFloat': {'readonly': True},
    u'parseInt': {'readonly': True},

    u'eval': {'dangerous': DANGEROUS_EVAL},
    u'Function': {'dangerous': DANGEROUS_EVAL},

    u'Object':
        {'value':
             {u'prototype': {'readonly': is_shared_scope},
              u'constructor':  # Just an experiment for now
                  {'value': lambda t: GLOBAL_ENTITIES['Function']}}},
    u'String':
        {'value':
             {u'prototype': {'readonly': is_shared_scope}},
         'return': call_definitions.string_global},
    u'Array':
        {'value':
             {u'prototype': {'readonly': is_shared_scope}},
         'return': call_definitions.array_global},
    u'Number':
        {'value':
             {u'prototype':
                  {'readonly': is_shared_scope},
              u'POSITIVE_INFINITY':
                  {'value': lambda t: JSWrapper(float('inf'), traverser=t)},
              u'NEGATIVE_INFINITY':
                  {'value': lambda t: JSWrapper(float('-inf'), traverser=t)}},
         'return': call_definitions.number_global},
    u'Boolean':
        {'value':
             {u'prototype': {'readonly': is_shared_scope}},
         'return': call_definitions.boolean_global},
    u'RegExp': {'value': {u'prototype': {'readonly': is_shared_scope}}},
    u'Date': {'value': {u'prototype': {'readonly': is_shared_scope}}},
    u'File': {'value': {u'prototype': {'readonly': is_shared_scope}}},

    u'Math':
        {'value':
             {u'PI':
                  {'value': lambda t: JSWrapper(math.pi, traverser=t)},
              u'E':
                  {'value': lambda t: JSWrapper(math.e, traverser=t)},
              u'LN2':
                  {'value': lambda t: JSWrapper(math.log(2), traverser=t)},
              u'LN10':
                  {'value': lambda t: JSWrapper(math.log(10), traverser=t)},
              u'LOG2E':
                  {'value': lambda t: JSWrapper(math.log(math.e, 2),
                                                traverser=t)},
              u'LOG10E':
                  {'value': lambda t: JSWrapper(math.log10(math.e),
                                                traverser=t)},
              u'SQRT2':
                  {'value': lambda t: JSWrapper(math.sqrt(2), traverser=t)},
              u'SQRT1_2':
                  {'value': lambda t: JSWrapper(math.sqrt(1/2), traverser=t)},
              u'abs':
                  {'return': python_wrap(abs, [('num', 0)])},
              u'acos':
                  {'return': python_wrap(math.acos, [('num', 0)])},
              u'asin':
                  {'return': python_wrap(math.asin, [('num', 0)])},
              u'atan':
                  {'return': python_wrap(math.atan, [('num', 0)])},
              u'atan2':
                  {'return': python_wrap(math.atan2, [('num', 0),
                                                      ('num', 1)])},
              u'ceil':
                  {'return': python_wrap(math.ceil, [('num', 0)])},
              u'cos':
                  {'return': python_wrap(math.cos, [('num', 0)])},
              u'exp':
                  {'return': python_wrap(math.exp, [('num', 0)])},
              u'floor':
                  {'return': python_wrap(math.floor, [('num', 0)])},
              u'log':
                  {'return': call_definitions.math_log},
              u'max':
                  {'return': python_wrap(max, [('num', 0)], nargs=True)},
              u'min':
                  {'return': python_wrap(min, [('num', 0)], nargs=True)},
              u'pow':
                  {'return': python_wrap(math.pow, [('num', 0),
                                                    ('num', 0)])},
              u'random': # Random always returns 0.5 in our fantasy land.
                  {'return': call_definitions.math_random},
              u'round':
                  {'return': call_definitions.math_round},
              u'sin':
                  {'return': python_wrap(math.sin, [('num', 0)])},
              u'sqrt':
                  {'return': python_wrap(math.sqrt, [('num', 1)])},
              u'tan':
                  {'return': python_wrap(math.tan, [('num', 0)])},
                  }},

    u'netscape':
        {'value':
             {u'security':
                  {'value':
                       {u'PrivilegeManager':
                            {'value':
                                 {u'enablePrivilege':
                                      {'dangerous': {
                                          'signing_help':
                                            'Any references to this API must '
                                            'be removed from your extension. '
                                            'Add-ons using this API will not '
                                            'be accepted for signing.',
                                          'signing_severity': 'high',
                                          'description': (
                                            'enablePrivilege is extremely '
                                            'dangerous, and nearly always '
                                            'unnecessary. It should not be '
                                            'used under any circumstances.'),
                                      }}}}}}}},
    u'navigator':
        {'value': {u'wifi': {'dangerous': True},
                   u'geolocation': {'dangerous': True}}},

    u'Components':
        {'dangerous_on_read':
             lambda t, e: bool(e.metadata.get('is_jetpack')),
         'value':
             {u'classes':
                  {'xpcom_wildcard': True,
                   'value':
                       {u'createInstance':
                           {'return': xpcom_const('createInstance')},
                        u'getService':
                           {'return': xpcom_const('getService')}}},
              'utils':
                  {'value': {u'evalInSandbox':
                                 {'dangerous': {
                                     'editors_only': 'true',
                                     'signing_help':
                                     DANGEROUS_EVAL['signing_help'],
                                     'signing_severity': 'low'}},
                             u'cloneInto':
                                 {'dangerous': {
                                     'editors_only': True,
                                     'signing_help': FUNCTION_EXPORT_HELP,
                                     'signing_severity': 'low',
                                     'description': (
                                         'Can be used to expose privileged '
                                         'functionality to unprivileged scopes. '
                                         'Care should be taken to ensure that '
                                         'this is done safely.')}},
                             u'exportFunction':
                                 {'dangerous': {
                                     'editors_only': True,
                                     'signing_help': FUNCTION_EXPORT_HELP,
                                     'signing_severity': 'low',
                                     'description': (
                                         'Can be used to expose privileged '
                                         'functionality to unprivileged scopes. '
                                         'Care should be taken to ensure that '
                                         'this is done safely.')}},
                             u'import':
                                 {'dangerous':
                                      lambda a, t, e:
                                          a and 'ctypes.jsm' in _get_as_str(t(a[0]))},

                             u'waiveXrays':
                                 {'return': call_definitions.js_unwrap}}},
              u'interfaces': {'value': INTERFACE_ENTITIES}}},
    u'extensions': {'dangerous': True},
    u'xpcnativewrappers': {'dangerous': True},

    u'XMLHttpRequest':
        {'value':
             {u'open':
                  {'dangerous':
                       # Ban synchronous XHR by making sure the third arg
                       # is absent and false.
                       lambda a, t, e:
                           a and len(a) >= 3 and
                           not t(a[2]).get_literal_value() and
                           'Synchronous HTTP requests can cause serious UI '
                           'performance problems, especially to users with '
                           'slow network connections.'}}},

    # Global properties are inherently read-only, though this formalizes it.
    u'Infinity':
        {'value':
             lambda t:
                 GLOBAL_ENTITIES[u'Number']['value'][u'POSITIVE_INFINITY']},
    u'NaN': {'readonly': True},
    u'undefined': {'readonly': True},

    u'innerHeight': {'readonly': False},
    u'innerWidth': {'readonly': False},
    u'width': {'readonly': False},
    u'height': {'readonly': False},
    u'top': {'readonly': actions._readonly_top},

    u'content':
        {'context': 'content',
         'value':
             {u'document':
                  {'value': lambda t: GLOBAL_ENTITIES[u'document']}}},
    u'contentWindow':
        {'context': 'content',
         'value':
             lambda t: {'value': GLOBAL_ENTITIES}},
    u'_content': {'value': lambda t: GLOBAL_ENTITIES[u'content']},
    u'gBrowser':
        {'value':
             {u'contentDocument':
                  {'context': 'content',
                   'value': lambda t: CONTENT_DOCUMENT},
              u'contentWindow':
                  {'value':
                       lambda t: {'value': GLOBAL_ENTITIES}},
              u'selectedTab':
                  {'readonly': False}}},
    u'opener':
        {'value':
             lambda t: {'value': GLOBAL_ENTITIES}},

    u'XPCNativeWrapper':
        {'value':
             {u'unwrap':
                  {'return': call_definitions.js_unwrap}},
         'return': call_definitions.js_wrap},

    # Preference creation in pref defaults files
    u'pref': {'dangerous': actions._call_create_pref},
    u'user_pref': {'dangerous': actions._call_create_pref},

    u'unsafeWindow': {'dangerous': 'The use of unsafeWindow is insecure and '
                                   'should be avoided whenever possible. '
                                   'Consider using a different API if it is '
                                   'available in order to achieve similar '
                                   'functionality.'},

    u'XPCOMUtils':
        {'value': {u'categoryManager': {'value': CATEGORY_MANAGER}}},
    u'updateCharsetPopupMenu': entity('updateCharsetPopupMenu'),
    u'EditorSetDocumentCharacterSet': entity('EditorSetDocumentCharacterSet'),
    u'DisablePhishingWarning': entity('DisablePhishingWarning'),
    u'RoomInfo': entity('RoomInfo'),
    u'FillInHTMLTooltip': entity('FillInHTMLTooltip'),
    u'escapeXMLchars': entity('escapeXMLchars'),
    u'getNonHtmlRecipients': entity('getNonHtmlRecipients'),
    u'updateCharsetPopupMenu': entity('updateCharsetPopupMenu'),
    u'EditorSetDocumentCharacterSet': entity('EditorSetDocumentCharacterSet'),
    u'awArrowHit': entity('awArrowHit'),
    u'UpdateMailEditCharset': entity('UpdateMailEditCharset'),
    u'InitCharsetMenuCheckMark': entity('InitCharsetMenuCheckMark'),
    u'allowRemoteContentForSender': entity('allowRemoteContentForSender'),
    u'allowRemoteContentForSite': entity('allowRemoteContentForSite'),
    u'createNewHeaderView': entity('createNewHeaderView'),


    u'MarionetteComponent': {'dangerous_on_read': MARIONETTE_MESSAGE},
    u'MarionetteServer': {'dangerous_on_read': MARIONETTE_MESSAGE},

    'Application': {'dangerous_on_read': fuel_error},
    'NewTabURL': {'value': {'override': entity('NewTabURL.override')}},

    # Common third-party libraries
    'Handlebars': {
        'value': {
            'SafeString':
                {'dangerous':
                    UNSAFE_TEMPLATE_METHOD % 'Handlebars.SafeString'}}},
    # Angular
    '$sce': {
        'value': {
            'trustAs': {'dangerous':
                            UNSAFE_TEMPLATE_METHOD % '$sce.trustAs'},
            'trustAsHTML': {'dangerous':
                                UNSAFE_TEMPLATE_METHOD % '$sce.trustAsHTML'}}},
}

CONTENT_DOCUMENT = GLOBAL_ENTITIES[u'content']['value'][u'document']
