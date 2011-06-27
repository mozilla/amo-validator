import math
import types

import spidermonkey
import instanceactions
import instanceproperties
from validator.decorator import versions_after
from jstypes import *


def _get_member_exp_property(traverser, node):
    """Return the string value of a member expression's property."""

    if node["property"]["type"] == "Identifier":
        return unicode(node["property"]["name"])
    else:
        eval_exp = traverser._traverse_node(node["property"])
        return unicode(eval_exp.get_literal_value())


def _expand_globals(traverser, node):
    """Expands a global object that has a lambda value."""

    if (node.is_global and
        "value" in node.value and
        isinstance(node.value["value"], types.LambdaType)):

        result = node.value["value"](t=traverser)
        return traverser._build_global("--", result)

    return node


def trace_member(traverser, node):
    "Traces a MemberExpression and returns the appropriate object"

    traverser._debug("TESTING>>%s" % node["type"])
    if node["type"] == "MemberExpression":
        # x.y or x[y]
        # x = base
        base = trace_member(traverser, node["object"])
        base = _expand_globals(traverser, base)

        # If we've got an XPCOM wildcard, just return the base, minus the WC
        if base.is_global and \
                "xpcom_wildcard" in base.value:
            traverser._debug("MEMBER_EXP>>XPCOM_WILDCARD")
            base.value = base.value.copy()
            del base.value["xpcom_wildcard"]
            return base

        identifier = _get_member_exp_property(traverser, node)
        test_identifier(traverser, identifier)
        traverser._debug("MEMBER_EXP>>PROPERTY: %s" % identifier)
        return base.get(traverser=traverser,
                        name=identifier)

    elif node["type"] == "Identifier":
        traverser._debug("MEMBER_EXP>>ROOT:IDENTIFIER")
        test_identifier(traverser, node["name"])
        output = traverser._seek_variable(node["name"])

        output = _expand_globals(traverser, output)

        return output
    else:
        traverser._debug("MEMBER_EXP>>ROOT:EXPRESSION")
        # It's an expression, so just try your damndest.
        traversed = traverser._traverse_node(node)
        if not isinstance(traversed, JSWrapper):
            return JSWrapper(traversed, traverser=traverser)
        return traversed


def test_identifier(traverser, name):
    "Tests whether an identifier is banned"

    import predefinedentities
    if name in predefinedentities.BANNED_IDENTIFIERS:
        traverser.err.warning(("testcases_scripting",
                               "create_identifier",
                               "banned_identifier"),
                              "Banned JavaScript Identifier",
                              ["An identifier was used in the JavaScript that "
                               "is not allowed due to security restrictions.",
                               "Identifier: %s" % name],
                              filename=traverser.filename,
                              line=traverser.line,
                              column=traverser.position,
                              context=traverser.context)


def _function(traverser, node):
    "Prevents code duplication"

    me = JSObject()

    # Replace the current context with a prototypeable JS object.
    traverser._pop_context()
    traverser._push_context(me)
    traverser._debug("THIS_PUSH")
    traverser.this_stack.append(me)  # Allow references to "this"

    # Declare parameters in the local scope
    params = []
    for param in node["params"]:
        if param["type"] == "Identifier":
            params.append(param["name"])
        elif param["type"] == "ArrayPattern":
            for element in param["elements"]:
                # Array destructuring in function prototypes? LOL!
                if element is None or element["type"] != "Identifier":
                    continue
                params.append(element["name"])

    local_context = traverser._peek_context(1)
    for param in params:
        var = JSWrapper(lazy=True, traverser=traverser)

        # We can assume that the params are static because we don't care about
        # what calls the function. We want to know whether the function solely
        # returns static values. If so, it is a static function.
        #var.dynamic = False
        local_context.set(param, var)

    traverser._traverse_node(node["body"])

    # Since we need to manually manage the "this" stack, pop off that context.
    traverser._debug("THIS_POP")
    traverser.this_stack.pop()

    return me


def _define_function(traverser, node):
    "Makes a function happy"

    me = _function(traverser, node)
    me = JSWrapper(value=me,
                   traverser=traverser,
                   callable=True)
    traverser._peek_context(2).set(node["id"]["name"], me)

    return True


def _func_expr(traverser, node):
    "Represents a lambda function"

    # Collect the result as an object
    results = _function(traverser, node)
    if not isinstance(results, JSWrapper):
        return JSWrapper(value=results, traverser=traverser)
    return results


def _define_with(traverser, node):
    "Handles `with` statements"

    object_ = traverser._traverse_node(node["object"])
    if isinstance(object_, JSWrapper) and \
       isinstance(object_.value, JSObject):
        traverser.contexts[-1] = object_.value
    return


def _define_var(traverser, node):
    "Creates a local context variable"

    traverser._debug("VARIABLE_DECLARATION")
    traverser.debug_level += 1

    for declaration in node["declarations"]:

        # It could be deconstruction of variables :(
        if declaration["id"]["type"] == "ArrayPattern":

            vars = []
            for element in declaration["id"]["elements"]:
                # NOTE : Multi-level array destructuring sucks. Maybe implement
                # it someday if you're bored, but it's so rarely used and it's
                # so utterly complex, there's probably no need to ever code it
                # up.
                if element is None or element["type"] != "Identifier":
                    vars.append(None)
                    continue
                vars.append(element["name"])

            # The variables are not initialized
            if declaration["init"] is None:
                # Simple instantiation; no initialization
                for var in vars:
                    if not var:
                        continue
                    traverser._set_variable(var, None)

            # The variables are declared inline
            elif declaration["init"]["type"] == "ArrayPattern":
                # TODO : Test to make sure len(values) == len(vars)
                for value in declaration["init"]["elements"]:
                    if vars[0]:
                        traverser._set_variable(
                                vars[0],
                                JSWrapper(traverser._traverse_node(value),
                                          traverser=traverser))
                    vars = vars[1:]  # Pop off the first value

            # It's being assigned by a JSArray (presumably)
            elif declaration["init"]["type"] == "ArrayExpression":

                assigner = traverser._traverse_node(declaration["init"])
                for value in assigner.value.elements:
                    if vars[0]:
                        traverser._set_variable(
                                vars[0],
                                value)
                    vars = vars[1:]

        elif declaration["id"]["type"] == "ObjectPattern":

            init = traverser._traverse_node(declaration["init"])

            def _proc_objpattern(init_obj, properties):
                for prop in properties:
                    # Get the name of the init obj's member
                    if prop["key"]["type"] == "Literal":
                        prop_name = prop["key"]["value"]
                    elif prop["key"]["type"] == "Identifier":
                        prop_name = prop["key"]["name"]
                    else:
                        continue

                    if prop["value"]["type"] == "Identifier":
                        traverser._set_variable(prop["value"]["name"],
                                                init_obj.get(traverser,
                                                             prop_name))
                    elif prop["value"]["type"] == "ObjectPattern":
                        _proc_objpattern(init_obj.get(traverser,
                                                      prop_name),
                                         prop["value"]["properties"])

            if init is not None:
                _proc_objpattern(init_obj=init,
                                 properties=declaration["id"]["properties"])
            #else:
                # FIXME : Is this even supposed to be possible?
                # No idea why this is happening,

        else:
            var_name = declaration["id"]["name"]
            traverser._debug("NAME>>%s" % var_name)

            var_value = traverser._traverse_node(declaration["init"])
            traverser._debug("VALUE>>%s" % (var_value.output()
                                            if var_value is not None
                                            else "None"))

            if not isinstance(var_value, JSWrapper):
                var = JSWrapper(value=var_value,
                                const=(node["kind"] == "const"),
                                traverser=traverser)
            else:
                var = var_value
                var.const = node["kind"] == "const"
            traverser._set_variable(var_name, var)

    traverser.debug_level -= 1

    # The "Declarations" branch contains custom elements.
    return True


def _define_obj(traverser, node):
    "Creates a local context object"

    var = JSObject()
    for prop in node["properties"]:
        var_name = ""
        key = prop["key"]
        if key["type"] == "Literal":
            var_name = key["value"]
        else:
            var_name = key["name"]
        var_value = traverser._traverse_node(prop["value"])
        var.set(var_name, var_value, traverser)

        # TODO: Observe "kind"

    if not isinstance(var, JSWrapper):
        return JSWrapper(var, lazy=True, traverser=traverser)
    var.lazy = True
    return var


def _define_array(traverser, node):
    "Instantiates an array object"

    arr = JSArray()
    for elem in node["elements"]:
        arr.elements.append(traverser._traverse_node(elem))

    return arr


def _define_literal(traverser, node):
    "Creates a JSVariable object based on a literal"
    value = node["value"]
    if isinstance(value, dict):
        return JSWrapper(traverser=traverser)
    return JSWrapper(JSLiteral(value), traverser=traverser)


def _call_expression(traverser, node):
    args = node["arguments"]

    for arg in args:
        traverser._traverse_node(arg)

    member = traverser._traverse_node(node["callee"])
    if (member.is_global and
        "dangerous" in member.value and
        isinstance(member.value["dangerous"], types.LambdaType)):

        dangerous = member.value["dangerous"]
        t = traverser._traverse_node
        result = dangerous(a=args, t=t, e=traverser.err)
        if result:
            # Generate a string representation of the params
            params = u", ".join([unicode(t(p).get_literal_value()) for
                                 p in args])
            traverser.err.warning(("testcases_javascript_actions",
                                   "_call_expression",
                                   "called_dangerous_global"),
                                  "Global called in dangerous manner",
                                  result if
                                    isinstance(result, types.StringTypes) else
                                  "A global function was called using a set "
                                  "of dangerous parameters. These parameters "
                                  "have been disallowed.",
                                  filename=traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)

    elif node["callee"]["type"] == "MemberExpression" and \
         node["callee"]["property"]["type"] == "Identifier":

        # If we can identify the function being called on any member of any
        # instance, we can use that to either generate an output value or test
        # for additional conditions.
        identifier_name = node["callee"]["property"]["name"]
        if identifier_name in instanceactions.INSTANCE_DEFINITIONS:
            result = instanceactions.INSTANCE_DEFINITIONS[identifier_name](
                        args, traverser, node)
            return result


    if member.is_global and "return" in member.value:
        return member.value["return"](wrapper=member,
                                      arguments=args,
                                      traverser=traverser)

    return True


def _call_settimeout(a, t, e):
    """
    Handler for setTimeout and setInterval. Should determine whether a[0]
    is a lambda function or a string. Strings are banned, lambda functions are
    ok. Since we can't do reliable type testing on other variables, we flag
    those, too.
    """

    return a and a[0]["type"] != "FunctionExpression"


def _readonly_top(t, r, rn):
    """Handle the readonly callback for window.top."""
    t.err.notice(
        err_id=("testcases_javascript_actions",
                "_readonly_top"),
        notice="window.top is a reserved variable",
        description="The 'top' global variable is reserved and cannot be "
                    "assigned any values starting with Firefox 6. Review your "
                    "code for any uses of the 'top' global, and refer to "
                    "https://bugzilla.mozilla.org/show_bug.cgi?id=654137 "
                    "for more information.",
        filename=t.filename,
        line=t.line,
        column=t.position,
        context=t.context,
        for_appversions={'{ec8030f7-c20a-464f-9b0e-13a3a9e97384}':
                             versions_after("firefox", "6.0a1")},
        compatibility_type="warning",
        tier=5)


def _expression(traverser, node):
    "Evaluates an expression and returns the result"
    result = traverser._traverse_node(node["expression"])
    if not isinstance(result, JSWrapper):
        return JSWrapper(result, traverser=traverser)
    return result


def _get_this(traverser, node):
    "Returns the `this` object"

    if not traverser.this_stack:
        return JSWrapper(traverser=traverser)

    return traverser.this_stack[-1]


def _new(traverser, node):
    "Returns a new copy of a node."

    # We don't actually process the arguments as part of the flow because of
    # the Angry T-Rex effect. For now, we just traverse them to ensure they
    # don't contain anything dangerous.
    args = node["arguments"]
    if isinstance(args, list):
        for arg in args:
            traverser._traverse_node(arg)
    else:
        traverser._traverse_node(args)

    elem = traverser._traverse_node(node["callee"])
    if not isinstance(elem, JSWrapper):
        elem = JSWrapper(elem, traverser=traverser)
    if elem.is_global:
        elem.value["overwriteable"] = True
    return elem


def _ident(traverser, node):
    "Initiates an object lookup on the traverser based on an identifier token"

    name = node["name"]

    # Ban bits like "newThread"
    test_identifier(traverser, name)

    if (traverser._is_local_variable(name) or
        traverser._is_global(name)):
        # This function very nicely wraps with JSWrapper for us :)
        found = traverser._seek_variable(name)
        return found

    # If the variable doesn't exist, we're going to create a placeholder for
    # it. The placeholder can have stuff assigned to it by things that work
    # like _expr_assignment
    result = JSWrapper(traverser=traverser, dirty=True)
    traverser._set_variable(name, result)
    return result


def _expr_assignment(traverser, node):
    "Evaluates an AssignmentExpression node."

    traverser._debug("ASSIGNMENT_EXPRESSION")
    traverser.debug_level += 1

    traverser._debug("ASSIGNMENT>>PARSING RIGHT")
    right = traverser._traverse_node(node["right"])
    right = JSWrapper(right, traverser=traverser)

    # Treat direct assignment different than augmented assignment.
    if node["operator"] == "=":

        global_overwrite = False
        readonly_value = True

        node_left = node["left"]
        traverser._debug("ASSIGNMENT:DIRECT(%s)" % node_left["type"])

        if node_left["type"] == "Identifier":
            # Identifiers just need the ID name and a value to push.
            # Raise a global overwrite issue if the identifier is global.
            global_overwrite = traverser._is_global(node_left["name"])

            # Get the readonly attribute and store its value if is_global
            if global_overwrite:
                from predefinedentities import GLOBAL_ENTITIES
                global_dict = GLOBAL_ENTITIES[node_left["name"]]
                readonly_value = (global_dict["readonly"] if
                                  "readonly" in global_dict else
                                  True)

            traverser._set_variable(node_left["name"], right)
        elif node_left["type"] == "MemberExpression":
            member_object = trace_member(traverser, node_left["object"])
            global_overwrite = (member_object.is_global and
                                not ("overwriteable" in member_object.value and
                                     member_object.value["overwriteable"]))

            member_property = _get_member_exp_property(traverser, node_left)
            traverser._debug("ASSIGNMENT:MEMBER_PROPERTY(%s)" % member_property)

            # Make sure to perform any setter operations.
            setter = instanceproperties.get_operation("set", member_property)
            if setter:
                right = setter(right, traverser) or right or None

            # Don't do the assignment if we're facing a global.
            if not global_overwrite:
                if member_object.value is None:
                    member_object.value = JSObject()

                if not member_object.is_global:
                    member_object.value.set(member_property, right)
                else:
                    # It's probably better to do nothing.
                    pass

            elif "value" in member_object.value:
                member_object_value = _expand_globals(traverser,
                                                      member_object).value
                if member_property in member_object_value["value"]:

                    # If it's a global and the actual member exists, test
                    # whether it can be safely overwritten.
                    member = member_object_value["value"][member_property]
                    readonly_value = (member["readonly"] if
                                      "readonly" in member else
                                      True)

        traverser._debug("ASSIGNMENT:DIRECT:GLOB_OVERWRITE %s" %
                             global_overwrite)

        if (global_overwrite and
            not traverser.is_jsm and
            readonly_value == True):

            traverser.err.warning(
                err_id=("testcases_javascript_actions",
                        "_expr_assignment",
                        "global_overwrite"),
                warning="Global variable overwrite",
                description="An attempt was made to overwrite a global "
                            "variable in some JavaScript code.",
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)

        if isinstance(readonly_value, types.LambdaType):
            # The readonly attribute supports a lambda function that accepts
            readonly_value(t=traverser, r=right, rn=node["right"])

        return right

    lit_right = right.get_literal_value()

    traverser._debug("ASSIGNMENT>>PARSING LEFT")
    left = traverser._traverse_node(node["left"])
    traverser._debug("ASSIGNMENT>>DONE PARSING LEFT")

    if isinstance(left, JSWrapper):
        lit_left = left.get_literal_value()

        # Don't perform an operation on None. Python freaks out
        if lit_left is None:
            lit_left = 0
        if lit_right is None:
            lit_right = 0

        if isinstance(lit_left, types.StringTypes) or \
           isinstance(lit_right, types.StringTypes):
            lit_left = unicode(lit_left)
            lit_right = unicode(lit_right)

        gleft = _get_as_num(left)
        gright = _get_as_num(right)
        # All of the assignment operators
        operators = {"=": lambda: right,
                     "+=": lambda: lit_left + lit_right,
                     "-=": lambda: gleft - gright,
                     "*=": lambda: gleft * gright,
                     "/=": lambda: 0 if gright == 0 else (gleft / gright),
                     "%=": lambda: 0 if gright == 0 else (gleft % gright),
                     "<<=": lambda: int(gleft) << int(gright),
                     ">>=": lambda: int(gleft) >> int(gright),
                     ">>>=": lambda: float(abs(int(gleft)) >> gright),
                     "|=": lambda: int(gleft) | int(gright),
                     "^=": lambda: int(gleft) ^ int(gright),
                     "&=": lambda: int(gleft) & int(gright)}

        token = node["operator"]
        traverser._debug("ASSIGNMENT>>OPERATION:%s" % token)
        if token not in operators:
            traverser._debug("ASSIGNMENT>>OPERATOR NOT FOUND")
            traverser.debug_level -= 1
            return left
        elif token in ("<<=", ">>=", ">>>=") and gright < 0:
            left.set_value(0, traverser=traverser)
            return left

        traverser._debug("ASSIGNMENT::L-value global? (%s)" %
                         ("Y" if left.is_global else "N"))
        new_value = operators[token]()
        traverser._debug("ASSIGNMENT::New value >> %s" % new_value)
        left.set_value(new_value, traverser=traverser)
        traverser.debug_level -= 1
        return left

    # Though it would otherwise be a syntax error, we say that 4=5 should
    # evaluate out to 5.
    traverser.debug_level -= 1
    return right


def _expr_binary(traverser, node):
    "Evaluates a BinaryExpression node."

    traverser.debug_level += 1

    # Select the proper operator.
    operator = node["operator"]
    traverser._debug("BIN_OPERATOR>>%s" % operator)

    # Traverse the left half of the binary expression.
    traverser._debug("BIN_EXP>>l-value")
    traverser.debug_level += 1

    left = traverser._traverse_node(node["left"])
    if not isinstance(left, JSWrapper):
        left = JSWrapper(left, traverser=traverser)
    traverser._debug("Is dirty? %r" % left.dirty)

    traverser.debug_level -= 1

    # Traverse the right half of the binary expression.
    traverser._debug("BIN_EXP>>r-value")
    traverser.debug_level += 1

    if (operator == "instanceof" and
        node["right"]["type"] == "Identifier" and
        node["right"]["name"] == "Function"):
        # We make an exception for instanceof's r-value if it's a dangerous
        # global, specifically Function.
        return JSWrapper(True, traverser=traverser)
    else:

        right = traverser._traverse_node(node["right"])
        if not isinstance(right, JSWrapper):
            right = JSWrapper(right, traverser=traverser)
        traverser._debug("Is dirty? %r" % right.dirty)

    # Dirty l or r values mean we can skip the expression. A dirty value
    # indicates that a lazy operation took place that introduced some
    # nondeterminacy.
    if left.dirty:
        return left
    elif right.dirty:
        return right

    traverser.debug_level -= 1

    # Binary expressions are only executed on literals.
    left_wrap = left
    left = left.get_literal_value()
    right_wrap = right
    right = right.get_literal_value()

    # Coerce the literals to numbers for numeric operations.
    gleft = _get_as_num(left)
    gright = _get_as_num(right)

    operators = {
        "==": lambda: left == right or gleft == gright,
        "!=": lambda: left != right,
        "===": lambda: left == right,
        "!==": lambda: not (type(left) == type(right) or left != right),
        ">": lambda: left > right,
        "<": lambda: left < right,
        "<=": lambda: left <= right,
        ">=": lambda: left >= right,
        "<<": lambda: int(gleft) << int(gright),
        ">>": lambda: int(gleft) >> int(gright),
        ">>>": lambda: float(abs(int(gleft)) >> int(gright)),
        "+": lambda: left + right,
        "-": lambda: gleft - gright,
        "*": lambda: gleft * gright,
        "/": lambda: 0 if gright == 0 else (gleft / gright),
        "%": lambda: 0 if gright == 0 else (gleft % gright),
        "in": lambda: right_wrap.contains(left),
        # TODO : implement instanceof
    }

    traverser.debug_level -= 1

    operator = node["operator"]
    output = None
    if (operator in (">>", "<<", ">>>") and
        ((left is None or right is None) or
         gright < 0)):
        output = False
    elif operator in operators:
        # Concatenation can be silly, so always turn undefineds into empty
        # strings and if there are strings, make everything strings.
        if operator == "+":
            if left is None:
                left = ""
            if right is None:
                right = ""
            if isinstance(left, types.StringTypes) or \
               isinstance(right, types.StringTypes):
                left = unicode(left)
                right = unicode(right)
        output = operators[operator]()

    if not isinstance(output, JSWrapper):
        return JSWrapper(output, traverser=traverser)
    return output


def _expr_unary(traverser, node):
    "Evaluates a UnaryExpression node"

    expr = traverser._traverse_node(node["argument"])
    expr_lit = expr.get_literal_value()
    expr_num = _get_as_num(expr_lit)

    operators = {"-": lambda: -1 * expr_num,
                 "+": expr_num,
                 "!": not expr_lit,
                 "~": -1 * (expr_num + 1),
                 "void": None,
                 "typeof": _expr_unary_typeof(expr),
                 "delete": None}  # We never want to empty the context


def _expr_unary_typeof(wrapper):
    "Evaluates the type of an object"

    if wrapper.callable:
        return "function"

    value = wrapper.value
    if value is None:
        return "undefined"
    elif isinstance(value, (JSObject, JSPrototype, JSArray)):
        return "object"
    elif isinstance(value, JSLiteral):
        value = value.value

        if isinstance(value, (int, long, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, types.StringTypes):
            return "string"


def _get_as_num(value):
    "Returns the JS numeric equivalent for a value"

    if value is None:
        return False

    try:
        if isinstance(value, types.StringTypes):
            return float(value)
        elif isinstance(value, (int, float, long)):
            return value
        else:
            return int(value)

    except:
        return 0

