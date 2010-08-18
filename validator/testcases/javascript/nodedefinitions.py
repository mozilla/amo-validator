from validator.testcases.javascript.traverser import JSVariable, JSObject

#(branches,
# explicitly_dynamic,
# estab_context,
# action,
# returns, # as in yielding a value, not breaking execution
#)

DEFINITIONS = {
    "EmptyStatement":       ((), False, False, None, False),
    "DebuggerStatement":    ((), False, False, None, False),
    
    "Program":              (("body", ), False, True, None, False),
    "BlockStatement":       (("body", ), False, False, None, False),
    "ExpressionStatement":  (("expression", ), False, False, None, True),
    "IfStatement":          (("test",
                              "alternate",
                              "consequent"),
                             False, False, None, True),
    "LabeledStatement":     (("body", ), True, False, None, False),
    "BreakStatement":       ((), False, False, None, False),
    "ContinueStatement":    ((), False, False, None, False),
    "WithStatement":        (("body", "object"),
                             False, False, _define_with, True),
    "SwitchStatement":      (("test", "cases"), False, False, None, False),
    "ReturnStatement":      (("argument", ), False, False, None, False),
    "ThrowStatement" :      (("argument", ), True, False, None, False),
    # The TryStatements are explecitly dynamic because I have no freakin idea
    # how to do static analysis on exception handling.
    "TryStatement":         (("block", "handler", "finalizer"),
                             True, False, None, False),
    "WhileStatement":       (("test", "body"), False, False, None, False),
    "DoWhileStatement":     (("test", "body"), False, False, None, False),
    "ForStatement":         (("init", "test", "update"),
                             False, False, None, False),
    "ForInStatement":       (("left", "right", "body"),
                             False, False, None, False),
    
    "FunctionDeclaration":  (("body", ),
                             False, True, _define_function, False),
    "VariableDeclaration":  (("declarations", ),
                             False, False, _define_var, False),
    
    "ThisExpression":       ((), False, False, None, True),
    "ArrayExpression":      (("elements", ), False, False, None, True),
    "ObjectExpression":     (("properties", ),
                             False, False, _define_obj, True),
    "FunctionExpression":   (("body", ),
                             False, True, _define_function, True),
    "SequenceExpression":   (("expressions", ),
                             False, False, None, True),
    "UnaryExpression":      (("argument", ),
                             False, False, None, True),
    "BinaryExpression":     (("left", "right"),
                             False, False, None, True),
    "AssignmentExpression": (("left", "right"),
                             False, False, None, True),
    "UpdateExpression":     (("argument", ),
                             False, False, None, True),
    "LogicalExpression":    (("left", "right"),
                             False, False, None, True),
    "ConditionalExpression":(("test", "alternate", "consequent"),
                             False, False, None, True),
    "NewExpression":        (("constructor", "arguments"),
                             False, False, None, True),
    "CallExpression":       (("callee", "arguments"),
                             False, False, None, True),
    "MemberExpression":     (("object", "property"),
                             False, False, None, True),
    "YieldExpression":      (("argument"), True, False, None, True),
    "ComprehensionExpression":
                            (("body", "filter"), False, False, None, True),
    "GeneratorExpression":  (("body", "filter"), False, False, None, True),
    "GraphExpression":      ((), True, False, None, False),
    "GraphIndexExpression": ((), True, False, None, False),
    
    "ObjectPattern":        ((), False, False, None, False),
    "ArrayPattern":         ((), False, False, None, False),
    
    "SwitchCase":           (("test", "consequent"),
                             False, False, None, False),
    "CatchClause":          (("param", "guard", "body"),
                             True, False, None, True),
    "ComprehensionBlock":   (("left", "right"), False, False, None, True),
    
    "Identifier":           ((), False, False, None, True),
    "Literal":              ((), False, False, None, True),
    "UnaryOperator":        ((), False, False, None, True),
    "BinaryOperator"        ((), False, False, None, True),
    "LogicalOperator":      ((), False, False, None, True),
    "AssignmentOperator":   ((), False, False, None, True),
    "UpdateOperator":       ((), False, False, None, True)
    
    # E4X? What E4X? I have no idea what you're talking about. There's no E4X
    # here. Move along now, move along.
    
}

def _define_function(traverser, node):
    "Makes a function happy"
    
    params = []
    for param in node["params"]:
        params.append(param["name"])
    
    local_context = traverser._peek_context()
    for param in params:
        var = Variable(traverser.err)
        
        # We can assume that the params are static because we don't care about
        # what calls the function. We want to know whether the function solely
        # returns static values. If so, it is a static function.
        var.dynamic = False
        local_context[param] = var

def _define_with(traverser, node):
    "Handles `with` statements"
    
    object_ = traverser._traverse_node(node["object"])
    if not isinstance(object_, JSObject):
        # If we don't get an object back (we can't deal with literals), then
        # just fall back on standard traversal.
        return False
    
    traverser.contexts[-1] = object_
