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
from validator.compat import (FX10_DEFINITION, FX29_DEFINITION,
                              FX30_DEFINITION, FX31_DEFINITION,
                              FX33_DEFINITION, FX36_DEFINITION)
from validator.constants import BUGZILLA_BUG, MDN_DOC
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
            err_id=("js", "instanceactions", "addEventListener_fourth"),
            notice="`addEventListener` called with truthy fourth argument.",
            description="When called with a truthy forth argument, listeners "
                        "can be triggered potentially unsafely by untrusted "
                        "code. This requires careful review.",
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
    if first_as_str.lower() == u"script":
        _create_script_tag(traverser)
    elif not simple_args[0].is_literal():
        _create_variable_element(traverser)


def createElementNS(args, traverser, node, wrapper):
    """Handles createElementNS calls"""

    if not args or len(args) < 2:
        return

    simple_args = map(traverser._traverse_node, args)

    second_as_str = actions._get_as_str(simple_args[1].get_literal_value())
    if "script" in second_as_str.lower():
        _create_script_tag(traverser)
    elif not simple_args[1].is_literal():
        _create_variable_element(traverser)


def createEvent(args, traverser, node, wrapper):
    """Handles createEvent calls."""

    if len(args) == 1 and args[0].get("value") == "DataContainerEvent":
        traverser.warning(
            err_id=("js", "instanceactions", "createEvent_DataContainerEvent"),
            warning="`DataContainerEvent` is no longer available",
            description="`DataContainerEvent` is no longer available. You "
                        "should use `MessageEvent` or `CustomEvent` instead. "
                        "See %s for more information." % BUGZILLA_BUG % 980134,
            for_appversions=FX31_DEFINITION,
            compatibility_type="error",
            tier=5)


def QueryInterface(args, traverser, node, wrapper):
    """Handles QueryInterface calls"""

    if not args:
        return

    from call_definitions import xpcom_constructor
    return xpcom_constructor("QueryInterface", True, True)(
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
    return xpcom_constructor("getInterface")(
        wrapper=node,
        arguments=args,
        traverser=traverser)


def _create_script_tag(traverser):
    """Raises a warning that the dev is creating a script tag"""
    traverser.err.warning(
        err_id=("testcases_javascript_instanceactions", "_call_expression",
                "called_createelement"),
        warning="createElement() used to create script tag",
        description="Dynamic creation of script nodes can be unsafe if "
                    "contents are not static or are otherwise unsafe, "
                    "or if `src` is remote.",
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def _create_variable_element(traverser):
    """Raises a warning that the dev is creating an arbitrary element"""
    traverser.err.warning(
        err_id=("testcases_javascript_instanceactions", "_call_expression",
                "createelement_variable"),
        warning="Variable element type being created",
        description=["createElement or createElementNS were used with a "
                     "variable rather than a raw string. Literal values "
                     "should be used when taking advantage of the element "
                     "creation functions.",
                     "E.g.: createElement('foo') rather than "
                     "createElement(el_type)"],
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
    if first_as_str.lower().startswith("on"):
        traverser.err.notice(
            err_id=("testcases_javascript_instanceactions", "setAttribute",
                    "setting_on*"),
            notice="on* attribute being set using setAttribute",
            description="To prevent vulnerabilities, event handlers (like "
                        "'onclick' and 'onhover') should always be defined "
                        "using addEventListener.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


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
    _set_HTML_property("insertAdjacentHTML", content, traverser)


def isSameNode(args, traverser, node, wrapper):
    """Raise an error when an add-on uses node.isSameNode(foo)."""
    traverser.err.error(
        err_id=("testcases_javascript_instanceactions", "isSameNode"),
        error="isSameNode function has been removed in Gecko 10.",
        description='The "isSameNode" function has been removed. You can use '
                    'the === operator as an alternative. See %s for more '
                    'information.' % BUGZILLA_BUG % 687400,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


def openDialog(args, traverser, node, wrapper):
    """Raise an error if the first argument is a remote URL."""
    if not args:
        return
    uri = traverser._traverse_node(args[0])
    from call_definitions import open_in_chrome_context
    open_in_chrome_context(uri, "openDialog", traverser)


def replaceWholeText(args, traverser, node, wrapper):
    """Raise an error when an add-on uses node.replaceWholeText(foo)."""
    traverser.err.error(
        err_id=("testcases_javascript_instanceactions", "replaceWholeText"),
        error="replaceWholeText function has been removed in Gecko 10.",
        description='The "replaceWholeText" function has been removed. See '
                    '%s for more information.' % BUGZILLA_BUG % 683482,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


def PageMod(args, traverser, node, wrapper):
    """
    This is the function that is called in Jetpack to modify the contents of a
    page with a "content script". This function needs to analyze he first
    parameter. If it is an object and if that object contains a "contentScript"
    string, that string needs to be passed to the validator.testcases.scripting
    library for testing as its own JS script file.
    """

    if not args:
        return

    pm_properties = traverser._traverse_node(args[0])
    if not pm_properties.has_property("contentScript"):
        return

    content_script = pm_properties.get(traverser, "contentScript")
    if not content_script.is_literal():
        return
    content_script = actions._get_as_str(content_script.get_literal_value())
    if not content_script.strip():
        return

    import validator.testcases.scripting as sub_scripting
    sub_scripting.test_js_file(
        traverser.err, traverser.filename, content_script,
        line=traverser.line, context=traverser.context)


def bind(args, traverser, node, wrapper):
    if "callee" not in node and "object" not in node["callee"]:
        return
    obj = traverser._traverse_node(node["callee"]["object"])
    if obj.callable:
        return obj


SYNCHRONOUS_SQL_DESCRIPTION = (
    "The use of synchronous SQL via the storage system leads to severe "
    "responsiveness issues, and should be avoided at all costs. Please "
    "use asynchronous SQL via Sqlite.jsm (http://mzl.la/sqlite-jsm) or "
    "the `executeAsync` method, or otherwise switch to a simpler database "
    "such as JSON files or IndexedDB.")


def _check_dynamic_sql(args, traverser, node=None, wrapper=None):
    """
    Checks for the use of non-static strings when creating/exeucting SQL
    statements.
    """

    simple_args = map(traverser._traverse_node, args)
    if len(args) >= 1 and not simple_args[0].is_literal():
        traverser.warning(
            err_id=("js", "instanceactions", "executeSimpleSQL_dynamic"),
            warning="SQL statements should be static strings",
            description=["Dynamic SQL statement should be constucted via "
                         "static strings, in combination with dynamic "
                         "parameter binding via Sqlite.jsm wrappers "
                         "(http://mzl.la/sqlite-jsm) or "
                         "`createAsyncStatement` "
                         "(https://developer.mozilla.org/en-US/docs"
                         "/Storage#Binding_parameters)"],
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
    return build_quick_xpcom("createInstance", "mozIStorageBaseStatement",
                             traverser, wrapper=True)


def executeSimpleSQL(args, traverser, node, wrapper):
    """
    Handles calls to `executeSimpleSQL`, warning that asynchronous methods
    should be used instead.
    """
    _check_dynamic_sql(args, traverser)
    traverser.err.warning(
        err_id=("js", "instanceactions", "executeSimpleSQL"),
        warning="Synchronous SQL should not be used",
        description=SYNCHRONOUS_SQL_DESCRIPTION,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def livemarkCallback(arguments, traverser, node, wrapper):
    """
    Handle calls to addLivemark, removeLivemark and getLivemark that pass
    callbacks.
    """
    bug = BUGZILLA_BUG % 896193
    mdn = MDN_DOC % "Mozilla/JavaScript_code_modules/Promise.jsm"
    if len(arguments) > 1:
        traverser.err.warning(
            err_id=("js", "instanceactions", "livemark_callback"),
            warning="Passing a callback to `addLivemark`, `removeLivemark` or "
                    "`getLivemark` is deprecated.",
            description="The asynchronous callbacks in these livemark "
                        "functions are now deprecated. The functions now "
                        "return promises that should be used instead. See {b} "
                        "and {m} for more information.".format(b=bug, m=mdn),
            compatibility_type='warning',
            for_appversions=FX29_DEFINITION,
            tier=3,
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def setPrototypeOfCallback(arguments, traverser, node, wrapper):
    traverser.warning(
        err_id=("testcases_javascript_instanceproperties", "setPrototypeOf"),
        warning="Using __proto__ or setPrototypeOf to set a prototype is now "
                "deprecated.",
        description="Using __proto__ or setPrototypeOf to set a prototype is "
                    "now deprecated. You should use Object.create instead. "
                    "See bug %s for more information." % BUGZILLA_BUG % 948227,
        for_appversions=FX30_DEFINITION,
        compatibility_type="warning",
        tier=5)


def sendAsBinary(arguments, traverser, node, wrapper):
    traverser.warning(
        err_id=("testcases_javascript_instanceproperties", "sendAsBinary"),
        warning="`sendAsBinary` is deprecated",
        description="`sendAsBinary` is deprecated and will be removed in a "
                    "future version of Firefox. Setting the appropriate "
                    "content-type or passing a Blob are possible alternatives."
                    "See bug %s for more information." % BUGZILLA_BUG % 939323,
        for_appversions=FX31_DEFINITION,
        compatibility_type="warning",
        tier=5)


def setup_nsISessionStoreFunc(name, arg_count, full_name):
    def was_called(arguments, traverser, node, wrapper):
        if len(arguments) == arg_count:
            string_arg = arguments[-1]
            if string_arg['type'] == 'Identifier':
                variable = traverser._seek_variable(string_arg['name'])
                value = variable.get_literal_value()
                if value == '[object Object]':
                    value = None  # Not a string, show warning.
            elif string_arg['type'] == 'Literal':
                value = string_arg['value']
            else:
                value = None  # We don't know what it is, warn the user.
            if not isinstance(value, (str, unicode)):
                traverser.warning(
                    err_id=("js", "entities", full_name),
                    warning="`{name}` must take a string as the last "
                            "argument".format(name=name),
                    description="`%s` now only accepts a string as "
                                "the last argument. See %s for more "
                                "information." % (name, BUGZILLA_BUG)
                                               % 996053,
                    for_appversions=FX33_DEFINITION,
                    compatibility_type="warning",
                    tier=5)
    return was_called


def os_file_readTo_callback(argument, traverser, node, wrapper):
    traverser.warning(
        err_id=("js", "entities", "os_file_readto"),
        warning="The readTo function in OS.File has been removed.",
        description="The readTo function in OS.File has been removed. "
                    "See %s for more information." % BUGZILLA_BUG % 1075438,
        for_appversions=FX36_DEFINITION,
        compatibility_type="error",
        tier=5)


INSTANCE_DEFINITIONS = {
    "addEventListener": addEventListener,
    "bind": bind,
    "createElement": createElement,
    "createElementNS": createElementNS,
    "createEvent": createEvent,
    "createAsyncStatement": _check_dynamic_sql,
    "createStatement": createStatement,
    "executeSimpleSQL": executeSimpleSQL,
    "getAsBinary": nsIDOMFile_deprec,
    "getAsDataURL": nsIDOMFile_deprec,
    "getInterface": getInterface,
    "insertAdjacentHTML": insertAdjacentHTML,
    "isSameNode": isSameNode,
    "openDialog": openDialog,
    "PageMod": PageMod,
    "QueryInterface": QueryInterface,
    "replaceWholeText": replaceWholeText,
    "setAttribute": setAttribute,
    "addLivemark": livemarkCallback,
    "removeLivemark": livemarkCallback,
    "getLivemark": livemarkCallback,
    "setPrototypeOf": setPrototypeOfCallback,
    "sendAsBinary": sendAsBinary,
    "setTabValue": setup_nsISessionStoreFunc(
        "setTabValue", 3, "nsISessionStore.setTabValue"),
    "setWindowValue": setup_nsISessionStoreFunc(
        "setWindowValue", 3, "nsISessionStore.setWindowValue"),
    "setGlobalValue": setup_nsISessionStoreFunc(
        "setGlobalValue", 2, "nsISessionStore.setGlobalValue"),
    "readTo": os_file_readTo_callback,
}
