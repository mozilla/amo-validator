import copy
import types

import traverser as js_traverser

def trace_member(traverser, node):
    "Traces a MemberExpression and returns the appropriate object"
    
    if node["type"] == "MemberExpression":
        # x.y or x[y]
        base = trace_member(traverser, node["object"])
        base = js_traverser.JSWrapper(base, traverser=traverser)

        # base = x
        if node["property"]["type"] == "Identifier":
            # y = token identifier
            return base.get(traverser=traverser,
                            name=node["property"]["name"])
        else:
            # y = literal value
            property = traverser._traverse_node(node["property"])
            return property.get_literal_value()

    elif node["type"] == "Identifier":
        traverser._debug("MEMBER_EXP>>ROOT:IDENTIFIER")
        return traverser._seek_variable(node["name"])
    else:
        traverser._debug("MEMBER_EXP>>ROOT:EXPRESSION")
        # It's an expression, so just try your damndest.
        return js_traverser.JSWrapper(traverser._traverse_node(node),
                                      traverser=traverser)

def _function(traverser, node):
    "Prevents code duplication"
    
    me = js_traverser.JSObject()
    
    # Replace the current context with a prototypeable JS object.
    traverser._pop_context()
    traverser._push_context(me)
    traverser._debug("THIS_PUSH")
    traverser.this_stack.append(me) # Allow references to "this"
    
    # Declare parameters in the local scope
    params = []
    for param in node["params"]:
        if param["type"] == "Identifier":
            params.append(param["name"])
        elif param["type"] == "ArrayPattern":
            for element in param["elements"]:
                params.append(element["name"])
    
    local_context = traverser._peek_context(2)
    for param in params:
        var = js_traverser.JSWrapper(lazy=True, traverser=traverser)
        
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
    traverser._peek_context(2).set(node["id"]["name"], me)
    
    return True

def _func_expr(traverser, node):
    "Represents a lambda function"
    
    # Collect the result as an object
    results = _function(traverser, node)
    return js_traverser.JSWrapper(value=results, traverser=traverser)

def _define_with(traverser, node):
    "Handles `with` statements"
    
    object_ = traverser._traverse_node(node["object"])
    if not isinstance(object_, traverser.JSObject):
        # If we don't get an object back (we can't deal with literals), then
        # just fall back on standard traversal.
        return False
    
    traverser.contexts[-1] = object_

def _define_var(traverser, node):
    "Creates a local context variable"
    
    traverser._debug("VARIABLE_DECLARATION")
    traverser.debug_level += 1
    
    for declaration in node["declarations"]:

        # It could be deconstruction of variables :(
        if declaration["id"]["type"] == "ArrayPattern":
            
            vars = []
            for element in declaration["id"]["elements"]:
                vars.append(element["name"])

            # The variables are not initialized
            if declaration["init"] is None:
                # Simple instantiation; no initialization
                for var in vars:
                    traverser._set_variable(var, None)

            # The variables are declared inline
            elif declaration["init"]["type"] == "ArrayPattern":
                # TODO : Test to make sure len(values) == len(vars)
                for value in declaration["init"]["elements"]:
                    traverser._set_variable(var[0],
                                            js_traverser.JSWrapper(
                                                traverser._traverse_node(value),
                                                traverser=traverser))
                    var = var[1:] # Pop off the first value

            # It's being assigned by a JSArray (presumably)
            else:
                pass
                # TODO : Once JSArray is fully implemented, do this!


        else:
    
            var_name = declaration["id"]["name"]
            traverser._debug("NAME>>%s" % var_name)
            
            var_value = traverser._traverse_node(declaration["init"])
            traverser._debug("VALUE>>%s" % (var_value.output()
                                            if var_value is not None
                                            else "None"))
    
            var = js_traverser.JSWrapper(value=var_value,
                                         const=(node["kind"]=="const"),
                                         traverser=traverser)
            traverser._set_variable(var_name, var)
            
    traverser.debug_level -= 1
    
    # The "Declarations" branch contains custom elements.
    return True

def _define_obj(traverser, node):
    "Creates a local context object"
    
    var = js_traverser.JSObject()
    for prop in node["properties"]:
        var_name = ""
        key = prop["key"]
        if key["type"] == "Literal":
            var_name = key["value"]
        else:
            var_name = key["name"]
        var_value = traverser._traverse_node(prop["value"])
        var.set(var_name, var_value)
        
        # TODO: Observe "kind"
    
    return js_traverser.JSWrapper(var, lazy=True, traverser=traverser)

def _define_array(traverser, node):
    "Instantiates an array object"
    
    arr = js_traverser.JSArray()
    for elem in node["elements"]:
        arr.elements.append(traverser._traverse_node(elem))
    
    return arr

def _define_literal(traverser, node):
    "Creates a JSVariable object based on a literal"

    var = js_traverser.JSLiteral(node["value"])
    return js_traverser.JSWrapper(var, traverser=traverser)

def _call_expression(traverser, node):
    args = node["arguments"]

    member = traverser._traverse_node(node["callee"])
    if member.is_global and \
       "dangerous" in member.value and \
       isinstance(member.value["dangerous"], types.LambdaType):
        dangerous = member.value["dangerous"]

        t = traverser._traverse_node
        result = dangerous(a=args, t=t)
        if result:
            # Generate a string representation of the params
            params = ", ".join([str(t(p).get_literal_value()) for p in args])
            traverser.err.warning(("testcases_javascript_actions",
                                   "_call_expression",
                                   "called_dangerous_global"),
                                  "Global called in dangerous manner",
                                  ["A global function was called using a set "
                                   "of dangerous parameters. These parameters "
                                   "have been disallowed.",
                                   "Params: %s" % params],
                                  traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)
    elif node["callee"]["type"] == "MemberExpression" and \
         node["callee"]["property"]["type"] == "Identifier":
        identifier_name =  node["callee"]["property"]["name"]
        simple_args = [str(traverser._traverse_node(a).get_literal_value()) for
                       a in
                       args]
        if (identifier_name == "createElement" and
            simple_args[0] == "script") or \
           (identifier_name == "createElementNS" and
            "script" in simple_args[1]):
            traverser.err.warning(("testcases_javascript_actions",
                                   "_call_expression",
                                   "called_createelement"),
                                  "createElement() used to create script tag"
                                  "The createElement() function was used to "
                                  "create a script tag in a JavaScript file. "
                                  "Add-ons are not allowed to create script "
                                  "tags or load code dynamically from the web.",
                                  traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)
    return True

def _call_settimeout(a,t):
    """Handler for setTimeout and setInterval. Should determine whether a[0]
    is a lambda function or a string. Strings are banned, lambda functions are
    ok. Since we can't do reliable type testing on other variables, we flag
    those, too."""

    return (not a) or a[0]["type"] != "FunctionExpression"

def _expression(traverser, node):
    "Evaluates an expression and returns the result"
    result = traverser._traverse_node(node["expression"])
    return js_traverser.JSWrapper(result, traverser=traverser)
    
def _get_this(traverser, node):
    "Returns the `this` object"
    
    if not traverser.this_stack:
        return js_traverser.JSWrapper(traverser=traverser)
    
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
    elem = js_traverser.JSWrapper(elem, traverser=traverser)
    return elem

def _ident(traverser, node):
    "Initiates an object lookup on the traverser based on an identifier token"

    name = node["name"]
    if traverser._is_local_variable(name) or \
       traverser._is_global(name):
        # This function very nicely wraps with JSWrapper for us :)
        found = traverser._seek_variable(name)
        return found

    # If the variable doesn't exist, we're going to create a placeholder for
    # it. The placeholder can have stuff assigned to it by things that work
    # like _expr_assignment
    result = js_traverser.JSWrapper(traverser=traverser)
    traverser._set_variable(name, result)
    return result

def _expr_assignment(traverser, node):
    "Evaluates an AssignmentExpression node."
    
    traverser._debug("ASSIGNMENT_EXPRESSION")
    traverser.debug_level += 1

    traverser._debug("ASSIGNMENT>>PARSING RIGHT")
    right = traverser._traverse_node(node["right"])
    right = js_traverser.JSWrapper(right, traverser=traverser)
    lit_right = right.get_literal_value()
    
    traverser._debug("ASSIGNMENT>>PARSING LEFT")
    left = traverser._traverse_node(node["left"])
    
    if isinstance(left, js_traverser.JSWrapper):
        lit_left = left.get_literal_value()
        
        # Don't perform an operation on None. Python freaks out
        if lit_left is None:
            lit_left = 0
        if lit_right is None:
            lit_right = 0

        if isinstance(lit_left, (str, unicode)) or \
           isinstance(lit_right, (str, unicode)):
            lit_left = str(lit_left)
            lit_right = str(lit_right)

        # All of the assignment operators
        operators = {"=":lambda:right,
                     "+=":lambda:lit_left + lit_right,
                     "-=":lambda:lit_left - lit_right,
                     "*=":lambda:lit_left * lit_right,
                     "/=":lambda:lit_left / lit_right,
                     "%=":lambda:lit_left % lit_right,
                     "<<=":lambda:lit_left << lit_right,
                     ">>=":lambda:lit_left >> lit_right,
                     ">>>=":lambda:math.fabs(lit_left) >> lit_right,
                     "|=":lambda:lit_left | lit_right,
                     "^=":lambda:lit_left ^ lit_right,
                     "&=":lambda:lit_left & lit_right}
        
        token = node["operator"]
        traverser._debug("ASSIGNMENT>>OPERATION:%s" % token)
        if token not in operators:
            traverser._debug("ASSIGNMENT>>OPERATOR NOT FOUND")
            traverser.debug_level -= 1
            return left
        
        traverser._debug("ASSIGNMENT::LEFT>>%s" % str(left.is_global))
        traverser._debug("ASSIGNMENT::RIGHT>>%s" % str(operators[token]()))
        left.set_value(operators[token](), traverser=traverser)
        traverser.debug_level -= 1
        return left
    
    # Though it would otherwise be a syntax error, we say that 4=5 should
    # evaluate out to 5.
    traverser.debug_level -= 1
    return right

def _expr_binary(traverser, node):
    "Evaluates a BinaryExpression node."
    
    traverser.debug_level += 1


    traverser._debug("BIN_EXP>>LEFT")
    traverser.debug_level += 1

    left = traverser._traverse_node(node["left"])
    left = js_traverser.JSWrapper(left, traverser=traverser)

    traverser.debug_level -= 1


    traverser._debug("BIN_EXP>>RIGHT")
    traverser.debug_level += 1

    right = traverser._traverse_node(node["right"])
    right = js_traverser.JSWrapper(right, traverser=traverser)

    traverser.debug_level -= 1
    
    left = left.get_literal_value()
    right = right.get_literal_value()

    operator = node["operator"]
    traverser._debug("BIN_OPERATOR>>%s" % operator)

    type_operators = (">>", "<<", ">>>")
    operators = {
        "==": lambda: left == right,
        "!=": lambda: left != right,
        "===": lambda: type(left) == type(right) and left == right,
        "!==": lambda: not (type(left) == type(right) or left != right),
        ">": lambda: left > right,
        "<": lambda: left < right,
        "<=": lambda: left <= right,
        ">=": lambda: left >= right,
        "<<": lambda: left << right,
        ">>": lambda: left >> right,
        ">>>": lambda: math.fabs(left) >> right,
        "+": lambda: left + right,
        "-": lambda: _get_as_num(left) - _get_as_num(right),
        "*": lambda: _get_as_num(left) * _get_as_num(right),
        "/": lambda: _get_as_num(left) / _get_as_num(right),
    }

    traverser.debug_level -= 1
    
    operator = node["operator"]
    output = None
    if operator in type_operators and (
       left is None or right is None):
        output = False
    elif operator in operators:
        try:
            traverser._debug("BIN_EXP>>OPERATION FAILED!")
            output = operators[operator]()
        except:
            return js_traverser.JSWrapper(traverser=traverser)

    return js_traverser.JSWrapper(output, traverser=traverser)


def _get_as_num(value):
    "Returns the JS numeric equivalent for a value"

    if value is None:
        return False

    try:
        if isinstance(value, str):
            return float(value)
        elif isinstance(value, int) or isinstance(value, float):
            return value
        else:
            return int(value)

    except:
        return 0

