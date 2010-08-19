import traverser

def _define_function(traverser, node):
    "Makes a function happy"
    
    params = []
    for param in node["params"]:
        params.append(param["name"])
    
    local_context = traverser._peek_context()
    for param in params:
        var = traverser.JSVariable(traverser.err)
        
        # We can assume that the params are static because we don't care about
        # what calls the function. We want to know whether the function solely
        # returns static values. If so, it is a static function.
        var.dynamic = False
        local_context[param] = var

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
    
    var = traverser.JSObject()
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

def _define_literal(traverser, node):
    "Creates a JSVariable object based on a literal"
    var = traverser.JSVariable()
    var.set_value(node["value"])
    return var

def _call_settimeout(traverser, *args):
    # TODO : Analyze args[0]. If it's a function, return false.
    return True
