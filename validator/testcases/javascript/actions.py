import copy

import traverser as js_traverser

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
        var = traverser.JSVariable()
        
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
    
    return _function(traverser, node)

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
    
    for declaration in node["declarations"]:
        var = js_traverser.JSVariable()
        var_name = declaration["id"]["name"]
        var_value = traverser._traverse_node(declaration["init"])
        var.set_value(traverser, var_value)
        
        if node["kind"] == "const":
            var.const = True
    
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
    
    return var

def _define_array(traverser, node):
    "Instantiates an array object"
    
    arr = js_traverser.JSArray()
    for elem in node["elements"]:
        arr.elements.append(traverser._traverse_node(elem))
    
    return arr

def _define_literal(traverser, node):
    "Creates a JSVariable object based on a literal"
    var = js_traverser.JSVariable()
    var.set_value(traverser, node["value"])
    return var

def _call_settimeout(traverser, *args):
    # TODO : Analyze args[0]. If it's a function, return false.
    if js_traverser.DEBUG:
        print "ACTIONS>>TIMEOUT>>>"
        print args
    return True

def _expression(traverser, node):
    "Evaluates an expression and returns the result"
    result = traverser._traverse_node(node["expression"])
    if result is None:
        result = js_traverser.JSVariable()
        result.set_value(traverser, None)
        return result
    else:
        return result
    
def _get_this(traverser, node):
    "Returns the `this` object"
    
    if not traverser.this_stack:
        return None
    
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
        return None
    return copy.deepcopy(elem)

def _ident(traverser, node):
    "Initiates an object lookup on the traverser based on an identifier token"
    return traverser._seek_variable(node["name"])

def _expr_binary(traverser, node):
    "Evaluates a BinaryExpression node."
    
    traverser.debug_level += 1

    traverser._debug("BIN_EXP>>LEFT")
    traverser.debug_level += 1
    left = traverser._traverse_node(node["left"])
    traverser.debug_level -= 1

    traverser._debug("BIN_EXP>>RIGHT")
    traverser.debug_level += 1
    right = traverser._traverse_node(node["right"])
    traverser.debug_level -= 1
    
    
    if not isinstance(left, js_traverser.JSVariable) or \
       not isinstance(right, js_traverser.JSVariable):
        # If we can't nail down a solid BinaryExpression, just fall back on
        # traversing everything by hand.
        return False

    left = left.value
    right = right.value

    operator = node["operator"]

    operators = {
        "+": lambda l,r: l + r,
        "==": lambda l,r: l == r,
        "!=": lambda l,r: not l == r,
        "===": lambda l,r: type(l) == type(r) and l == r,
        "!==": lambda l,r: not (type(l) == type(r) and l == r)
    }

    traverser.debug_level -= 1

    if node["operator"] in operators:
        return operators[operator](left, right)
    return False
