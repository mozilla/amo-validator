"""
Prototype
---------

args
    the raw list of arguments
traverser
    the traverser
node
    the current node being evaluated
"""

import actions
from instanceproperties import _set_HTML_property


def addEventListener(args, traverser, node, wrapper):
    """
    Handle calls to addEventListener and make sure that the fourth argument is
    falsey.
    """

    if not args or len(args) < 4:
        return

    fourth_arg = traverser._traverse_node(args[3])
    if fourth_arg.get_literal_value():
        traverser.err.notice(
            err_id=('js', 'instanceactions', 'addEventListener_fourth'),
            notice='`addEventListener` called with truthy fourth argument.',
            description='When called with a truthy forth argument, listeners '
                        'can be triggered potentially unsafely by untrusted '
                        'code. This requires careful review.',
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def createElement(args, traverser, node, wrapper):
    """Handles createElement calls"""

    if not args:
        return

    simple_args = map(traverser._traverse_node, args)

    first_as_str = actions._get_as_str(simple_args[0].get_literal_value())
    if first_as_str.lower() == u'script':
        _create_script_tag(traverser)
    elif not simple_args[0].is_literal():
        _create_variable_element(traverser)


def createElementNS(args, traverser, node, wrapper):
    """Handles createElementNS calls"""

    if not args or len(args) < 2:
        return

    simple_args = map(traverser._traverse_node, args)

    second_as_str = actions._get_as_str(simple_args[1].get_literal_value())
    if 'script' in second_as_str.lower():
        _create_script_tag(traverser)
    elif not simple_args[1].is_literal():
        _create_variable_element(traverser)


def QueryInterface(args, traverser, node, wrapper):
    """Handles QueryInterface calls"""

    if not args:
        return

    from call_definitions import xpcom_constructor
    return xpcom_constructor('QueryInterface', True, True)(
        wrapper=node,
        arguments=args,
        traverser=traverser)


def getInterface(args, traverser, node, wrapper):
    """Handles getInterface calls"""

    # This really only needs to be handled for nsIInterfaceRequestor
    # intarfaces, but as it's fair for code to assume that that
    # interface has already been queried and methods with this name
    # are unlikely to behave differently, we just process it for all
    # objects.

    if not args:
        return

    from call_definitions import xpcom_constructor
    return xpcom_constructor('getInterface')(
        wrapper=node,
        arguments=args,
        traverser=traverser)


def _create_script_tag(traverser):
    """Raises a warning that the dev is creating a script tag"""
    traverser.warning(
        err_id=('testcases_javascript_instanceactions', '_call_expression',
                'called_createelement'),
        warning='createElement() used to create script tag',
        description='Dynamic creation of script nodes can be unsafe if '
                    'contents are not static or are otherwise unsafe, '
                    'or if `src` is remote.',
        signing_help='Please avoid using <script> tags to load scripts. '
                     'For potential alternatives, please see '
                     'https://developer.mozilla.org/en-US/Add-ons/'
                     'Overlay_Extensions/XUL_School/'
                     'Appendix_D:_Loading_Scripts',
        signing_severity='medium')


def _create_variable_element(traverser):
    """Raises a warning that the dev is creating an arbitrary element"""
    traverser.err.warning(
        err_id=('testcases_javascript_instanceactions', '_call_expression',
                'createelement_variable'),
        warning='Variable element type being created',
        description=('createElement or createElementNS were used with a '
                     'variable rather than a raw string. Literal values '
                     'should be used when taking advantage of the element '
                     'creation functions.',
                     "E.g.: createElement('foo') rather than "
                     'createElement(el_type)'),
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def setAttribute(args, traverser, node, wrapper):
    """This ensures that setAttribute calls don't set on* attributes"""

    if not args:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    first_as_str = actions._get_as_str(simple_args[0].get_literal_value())
    if first_as_str.lower().startswith('on'):
        traverser.warning(
            err_id=('testcases_javascript_instanceactions', 'setAttribute',
                    'setting_on*'),
            warning='on* attribute being set using setAttribute',
            description='To prevent vulnerabilities, event handlers (like '
                        "'onclick' and 'onhover') should always be defined "
                        'using addEventListener.',
            signing_help='Please use `addEventListener` any place you might '
                         'otherwise create event listener attributes. Event '
                         'listener attributes will not be accepted in add-ons '
                         'submitted for automated signing in any instance '
                         'where they may be reasonably avoided.',
            signing_severity='medium')


def nsIDOMFile_deprec(args, traverser, node, wrapper):
    """A wrapper for call_definitions.nsIDOMFile_deprec."""
    from call_definitions import nsIDOMFile_deprec as cd_nsIDOMFile_deprec
    cd_nsIDOMFile_deprec(None, [], traverser)


def insertAdjacentHTML(args, traverser, node, wrapper):
    """
    Perfrom the same tests on content inserted into the DOM via
    insertAdjacentHTML as we otherwise would for content inserted via the
    various innerHTML/outerHTML properties.
    """
    if not args or len(args) < 2:
        return

    content = traverser._traverse_node(args[1])
    _set_HTML_property('insertAdjacentHTML', content, traverser)


def launch(args, traverser, node, wrapper):
    traverser.warning(
        err_id=('testcases_javascript_instanceactions', 'launch'),
        warning='Potentially dangerous use of `launch()`',
        description='Use of the `nsIFile.launch()` method can be dangerous, '
                    'and requires careful review.',
        editors_only=True)


def openDialog(args, traverser, node, wrapper):
    """Raise an error if the first argument is a remote URL."""
    if not args:
        return
    uri = traverser._traverse_node(args[0])
    from call_definitions import open_in_chrome_context
    open_in_chrome_context(uri, 'openDialog', traverser)


def bind(args, traverser, node, wrapper):
    if 'callee' not in node and 'object' not in node['callee']:
        return
    obj = traverser._traverse_node(node['callee']['object'])
    if obj.callable:
        return obj


SYNCHRONOUS_SQL_DESCRIPTION = (
    'The use of synchronous SQL via the storage system leads to severe '
    'responsiveness issues, and should be avoided at all costs. Please '
    'use asynchronous SQL via Sqlite.jsm (http://mzl.la/sqlite-jsm) or '
    'the `executeAsync` method, or otherwise switch to a simpler database '
    'such as JSON files or IndexedDB.')


def _check_dynamic_sql(args, traverser, node=None, wrapper=None):
    """
    Checks for the use of non-static strings when creating/exeucting SQL
    statements.
    """

    simple_args = map(traverser._traverse_node, args)
    if len(args) >= 1 and not simple_args[0].is_literal():
        traverser.warning(
            err_id=('js', 'instanceactions', 'executeSimpleSQL_dynamic'),
            warning='SQL statements should be static strings',
            description=('Dynamic SQL statement should be constucted via '
                         'static strings, in combination with dynamic '
                         'parameter binding via Sqlite.jsm wrappers '
                         '(http://mzl.la/sqlite-jsm) or '
                         '`createAsyncStatement` '
                         '(https://developer.mozilla.org/en-US/docs'
                         '/Storage#Binding_parameters)'),
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def createStatement(args, traverser, node, wrapper):
    """
    Handles calls to `createStatement`, returning an object which emits
    warnings upon calls to `execute` and `executeStep` rather than
    `executeAsync`.
    """
    _check_dynamic_sql(args, traverser)
    from predefinedentities import build_quick_xpcom
    return build_quick_xpcom('createInstance', 'mozIStorageBaseStatement',
                             traverser, wrapper=True)


def executeSimpleSQL(args, traverser, node, wrapper):
    """
    Handles calls to `executeSimpleSQL`, warning that asynchronous methods
    should be used instead.
    """
    _check_dynamic_sql(args, traverser)
    traverser.err.warning(
        err_id=('js', 'instanceactions', 'executeSimpleSQL'),
        warning='Synchronous SQL should not be used',
        description=SYNCHRONOUS_SQL_DESCRIPTION,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def create_preference_branch(arguments, traverser, node, wrapper):
    """Creates a preference branch, which can be used for testing composed
    preference names."""

    if arguments:
        arg = traverser._traverse_node(arguments[0])
        if arg.is_literal():
            # Avoid import loop
            from predefinedentities import build_quick_xpcom
            res = build_quick_xpcom('createInstance', 'nsIPrefBranch',
                                    traverser, wrapper=True)
            res.value['preference_branch'] = actions._get_as_str(arg)
            return res


def drop_pref_messages(wrapper):
    """Drop any preference-related messages for the given wrapper, if that
    wrapper is an immediate literal that was passed as an argument, and the
    messages are on the same line as the traverser.

    Used to ignore preference warnings when the strings are provably being
    read rather than written, or when they're provably being written and
    have a more useful, redundant warning already.
    """

    traverser = wrapper.traverser

    if wrapper.value.source == 'arguments':
        # Avoid import loop.
        from validator.testcases.regex import PREFERENCE_ERROR_ID

        for msg in wrapper.value.messages:
            if (msg['id'] == PREFERENCE_ERROR_ID and
                    (msg['file'], msg['line']) == (
                        traverser.filename, traverser.line)):
                traverser.err.drop_message(msg)


def get_preference(wrapper, arguments, traverser):
    """Tests get preference calls, and removes preference write warnings
    when they are not necessary."""

    if len(arguments) >= 1:
        arg = traverser._traverse_node(arguments[0])
        if arg.is_literal():
            drop_pref_messages(arg)


def set_preference(wrapper, arguments, traverser):
    """Tests set preference calls for non-root preferences branches against
    dangerous values."""

    if len(arguments) < 1:
        return

    parent = getattr(wrapper, 'parent', None)
    arg = traverser._traverse_node(arguments[0])
    if arg.is_literal():
        pref = actions._get_as_str(arg)

        # If we're being called on a preference branch other than the root,
        # prepend its branch name to the passed preference name.
        if (parent and parent.is_global and
                parent.value.get('preference_branch')):
            pref = parent.value['preference_branch'] + pref
        else:
            drop_pref_messages(arg)

        kw = {'err_id': ('testcases_javascript_actions',
                         '_call_expression', 'called_set_preference'),
              'warning': 'Attempt to set a dangerous preference'}

        # Local import to prevent import loop.
        from validator.testcases.regex import validate_pref
        validate_pref(pref, traverser, kw, wrapper=arg)

INSTANCE_DEFINITIONS = {
    'addEventListener': addEventListener,
    'bind': bind,
    'createElement': createElement,
    'createElementNS': createElementNS,
    'createAsyncStatement': _check_dynamic_sql,
    'createStatement': createStatement,
    'executeSimpleSQL': executeSimpleSQL,
    'getAsBinary': nsIDOMFile_deprec,
    'getAsDataURL': nsIDOMFile_deprec,
    'getBranch': create_preference_branch,
    'getDefaultBranch': create_preference_branch,
    'getInterface': getInterface,
    'insertAdjacentHTML': insertAdjacentHTML,
    'launch': launch,
    'openDialog': openDialog,
    'QueryInterface': QueryInterface,
    'setAttribute': setAttribute,
}
