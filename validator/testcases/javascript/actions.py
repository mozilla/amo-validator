import copy

import traverser as js_traverser

def node_has_global_root(traverser, node):
    "Determines whether a MemberExpression/Identifier is rooted as a global"
    
    # TODO : This should someday be worked into the various functions that
    # implement it. I feel like it's very inefficient to do a second lookup
    # when it's not necessary.
    if node["type"] == "MemberExpression":
        return node_has_global_root(traverser, node["object"])
    elif node["type"] == "Identifier":
        name = node["name"]
    
        # Test if it's an object in the current context
        if traverser._seek_local_variable(name) is not None:
            return False
    
        # Test if it's an object in the global scope
        return name in GLOBAL_ENTITIES

    else:
        # If we encounter an expression, just evaluate it and take the parser's
        # word for whether it's global or not.
        base = JSWrapper(traverser._traverse_node(node))
        return base.is_global

def trace_member(traverser, node):
    "Traces a MemberExpression and returns the appropriate object"
    
    if node["type"] == "MemberExpression":
        # x.y or x[y]
        base = trace_member(traverser, node["object"])
        
        # base = x
        if node["property"]["type"] == "Identifier":
            # y = token identifier
            return base.get(node["property"]["name"])
        else:
            # y = literal value
            property = traverser._traverse_node(node["property"])
            if isinstance(property, js_traverser.JSVariable):
                property_value = str(property)
                return base.get("property_value") if \
                       base.has_var(property_value) else \
                       None

    elif node["type"] == "Identifier":
        return traverser._seek_variable(node["name"])
    else:
        # It's an expression, so just try your damndest.
        return JSWrapper(traverser._traverse_node(node))

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
        params.append(param["name"])
    
    local_context = traverser._peek_context(2)
    for param in params:
        var = js_traverser.JSWrapper(lazy=True)
        
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
    traverser._peek_context(2)[node["id"]["name"]] = me
    
    return True

def _func_expr(traverser, node):
    "Represents a lambda function"
    
    # Collect the result as an object
    results = _function(traverser, node)
    return js_traverser.JSWrapper(value=results)

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
        var_name = declaration["id"]["name"]
        traverser._debug("NAME>>%s" % var_name)

        var_value = traverser._traverse_node(declaration["init"])
        if var_value is not None:
            traverser._debug("VALUE>>%s" % var_value.output())

        var = js_traverser.JSWrapper(value=var_value,
                                     const=(node["kind"]=="const"))
        traverser._set_variable(var_name, var)
    
    traverser.debug_level -= 1

    # The "Declarations" branch contains custom elements.
    return True

def _define_obj(traverser, node):
    "Creates a local context object"
    
    var = js_traverser.JSObject()
    for prop in node["properties"]:
        var_name = ""
        if prop["type"] == "Literal":
            var_name = prop["value"]
        else:
            var_name = prop["name"]
        var_value = traverser._traverse_node(node["value"])
        var[var_name] = var_value
        
        # TODO: Observe "kind"
    
    return js_traverser.JSWrapper(var, lazy=True)

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
    
    # We want to make sure of a few things. First, if it's not an identifier or
    # a MemberExpression, any sort of potentially dangerous object is going to
    # be tested somewhere else anyway. If it is one of those types, we want to
    # make sure it's a variable that we can actually analyze (i.e.: globals).
    if node["callee"]["type"] in ("Identifier", "MemberExpression") and \
       node_has_global_root(node["callee"]):
        # Yes; it's interesting and we should explore it.
        arguments = []
        for arg in args:
            arguments.append(traverser._traverse_node(arg))

    else:
        # No; just traverse it like any other tree.
        return False

    return True # We want to do all of the processing on our own

def _call_settimeout(traverser, *args):
    """Handler for setTimeout and setInterval. Should determine whether args[0]
    is a lambda function or a string. Strings are banned, lambda functions are
    ok."""
    
    return True

def _expression(traverser, node):
    "Evaluates an expression and returns the result"
    result = traverser._traverse_node(node["expression"])
    return js_traverser.JSWrapper(result)
    
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
    
    elem = traverser._traverse_node(node["constructor"])
    if elem is None:
        return js_traverser.JSWrapper()

    elem = js_traverser.JSWrapper(elem, traverser=traverser)
    return copy.deepcopy(elem)

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
    right = js_traverser.JSWrapper(right)
    lit_right = right.get_literal_value()
    
    traverser._debug("ASSIGNMENT>>PARSING LEFT")
    left = traverser._traverse_node(node["left"])
    
    if isinstance(left, js_traverser.JSWrapper):
        lit_left = left.get_literal_value()
        
        # Don't perform an operation on None. Python freaks out
        if lit_left is None:
            lit_left = 0
        
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
        
        traverser._debug("ASSIGNMENT>>OPERATION")
        token = node["operator"]
        if token not in operators:
            traverser._debug("ASSIGNMENT>>OPERATOR NOT FOUND")
            traverser.debug_level -= 1
            return left
        
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
    left = js_traverser.JSWrapper(left)

    traverser.debug_level -= 1


    traverser._debug("BIN_EXP>>RIGHT")
    traverser.debug_level += 1

    right = traverser._traverse_node(node["right"])
    right = js_traverser.JSWrapper(right)

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
        "-": lambda: left - right,
        "*": lambda: left * right,
        "/": lambda: left / right,
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


