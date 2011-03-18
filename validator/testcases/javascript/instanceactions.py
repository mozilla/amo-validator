from jstypes import *

# Prototype:
# - args: the raw list of arguments
# - traverser: the traverser
# - node: the current node being evaluated

def createElement(args, traverser, node):
    "Handles createElement calls"

    if not args:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if str(simple_args[0].get_literal_value()).lower() == "script":
        _create_script_tag(traverser)
    elif not (simple_args[0].is_literal() or
              isinstance(simple_args[0].get_literal_value(), str)):
        _create_variable_element(traverser)


def createElementNS(args, traverser, node):
    "Handles createElementNS calls"

    if not args or len(args) < 2:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if "script" in str(simple_args[1].get_literal_value()).lower():
        _create_script_tag(traverser)
    elif not (simple_args[1].is_literal() or
              isinstance(simple_args[1].get_literal_value(), str)):
        _create_variable_element(traverser)


def _create_script_tag(traverser):
    "Raises a warning that the dev is creating a script tag"
    traverser.err.warning(("testcases_javascript_instanceactions",
                           "_call_expression",
                           "called_createelement"),
                          "createElement() used to create script tag",
                          "The createElement() function was used to "
                          "create a script tag in a JavaScript file. "
                          "Add-ons are not allowed to create script "
                          "tags or load code dynamically from the "
                          "web.",
                          traverser.filename,
                          line=traverser.line,
                          column=traverser.position,
                          context=traverser.context)


def _create_variable_element(traverser):
    "Raises a warning that the dev is creating an arbitrary element"
    traverser.err.warning(("testcases_javascript_instanceactions",
                           "_call_expression",
                           "createelement_variable"),
                          "Variable element type being created",
                          ["createElement or createElementNS were "
                           "used with a variable rather than a raw "
                           "string. Literal values should be used "
                           "when taking advantage of the element "
                           "creation functions.",
                           "E.g.: createElement('foo') rather than "
                           "createElement(el_type)"],
                          traverser.filename,
                          line=traverser.line,
                          column=traverser.position,
                          context=traverser.context)


def setAttribute(args, traverser, node):
    "This ensures that setAttribute calls don't set on* attributes"

    if not args:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if str(simple_args[0].get_literal_value()).lower().startswith("on"):
        traverser.err.notice(("testcases_javascript_instanceactions",
                              "setAttribute",
                              "setting_on*"),
                             "on* attribute being set using setAttribute",
                             "To prevent vulnerabilities, event handlers "
                             "(like 'onclick' and 'onhover') should always "
                             "be defined using addEventListener.",
                             filename=traverser.filename,
                             line=traverser.line,
                             column=traverser.position,
                             context=traverser.context)


INSTANCE_DEFINITIONS = {"createElement": createElement,
                        "createElementNS": createElementNS,
                        "setAttribute": setAttribute}

