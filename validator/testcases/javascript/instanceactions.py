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

import types

import actions
from validator.compat import FX10_DEFINITION, FX14_DEFINITION
from validator.constants import BUGZILLA_BUG
from jstypes import *
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
            description="A falsey fourth argument indicates code that "
                        "accesses untrusted code. This code should be "
                        "further investigated.",
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
        description="The createElement() function was used to create a script "
                    "tag in a JavaScript file. Add-ons are not allowed to "
                    "create script tags or load code dynamically from the "
                    "web.",
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
                     "variable rather than a raw string. Literal values should "
                     "be used when taking advantage of the element creation "
                     "functions.",
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


INSTANCE_DEFINITIONS = {"addEventListener": addEventListener,
                        "createElement": createElement,
                        "createElementNS": createElementNS,
                        "getAsBinary": nsIDOMFile_deprec,
                        "getAsDataURL": nsIDOMFile_deprec,
                        "getInterface": getInterface,
                        "insertAdjacentHTML": insertAdjacentHTML,
                        "isSameNode": isSameNode,
                        "openDialog": openDialog,
                        "PageMod": PageMod,
                        "QueryInterface": QueryInterface,
                        "replaceWholeText": replaceWholeText,
                        "setAttribute": setAttribute}
