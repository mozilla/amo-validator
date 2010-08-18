
from validator.testcases.javascript.traverser import Variable

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
    "WithStatement":        (("body", "object"), False, False, None, True),
    "SwitchStatement":      (("test", "cases"), False, False, None, False),
    "ReturnStatement":      (("argument", ), False, False, None, False),
    "ThrowStatement" :      (("argument", ), True, False, None, False),
    # The TryStatements are explecitly dynamic because I have no freakin idea
    # how to do static analysis on exception handling.
    "TryStatement":         (("block",
                              "handler",
                              "finalizer"),
                             True, False, None, False),
    "WhileStatement":       (("test", "body"), False, False, None, False),
    "DoWhileStatement":     (("test", "body"), False, False, None, False),
    "ForStatement":         (("init",
                              "test",
                              "update"),
                             False, False, None, False),
    "ForInStatement":       (("left",
                              "right",
                              "body"), False, False, None, False),
    
    "FunctionDeclaration":  (("body", ), False, True, _define_function, True),
    "VariableDeclaration":  (("body", ), False, True, _define_var, False),
}

def _define_function(traverser, node):
    "Makes a function happy"
    
    params = []
    for param in node["params"]:
        params.append(param["name"])
    
    local_context = traverser._peek_context()
    for param in params:
        var = Variable()
        
        # We can assume that the params are static because we don't care about
        # what calls the function. We want to know whether the function solely
        # returns static values. If so, it is a static function.
        var.dynamic = False
        local_context[param] = var
