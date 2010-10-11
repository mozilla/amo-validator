import copy

import traverser as js_traverser

def _function(traverser, node):
    "Prevents code duplication"
    
    me = js_traverser.JSObject()
    
    traverser._pop_context()
    traverser._push_context(me)
    traverser.this_stack.append(me)
    
    params = []
    for param in node["params"]:
        params.append(param["name"])
    
    local_context = traverser._peek_context(2)
    for param in params:
        var = traverser.JSVariable(traverser.err)
        
        # We can assume that the params are static because we don't care about
        # what calls the function. We want to know whether the function solely
        # returns static values. If so, it is a static function.
        var.dynamic = False
        traverser._set_variable(param, var)
    
    traverser.this_stack.pop()
    
    return me

def _define_function(traverser, node):
    "Makes a function happy"
    
    me = _function(traverser, node)
    local_context[node["id"]["name"]] = me
    
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
        var = traverser.JSVariable()
        var_name = declaration["id"]["name"]
        var_value = traverser._traverse_node(node["init"])
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
    return traverser._traverse_node(node["expression"])
    
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
