import traverser
import actions

#(branches,
# explicitly_dynamic,
# estab_context,
# action,
# returns, # as in yielding a value, not breaking execution
# block_statement,
#)


DEFINITIONS = {
    "EmptyStatement":       ((), False, False, None, False, False),
    "DebuggerStatement":    ((), False, False, None, False, False),

    "Program":              (("body", ), False, True, None, False, True),
    "BlockStatement":       (("body", ), False, False, None, False, True),
    "ExpressionStatement":  (("expression", ),
                             False, False, actions._expression, True, False),
    "IfStatement":          (("test", "alternate", "consequent"),
                             False, False, None, True, True),
    "LabeledStatement":     (("body", ), True, False, None, False, False),
    "BreakStatement":       ((), False, False, None, False, False),
    "ContinueStatement":    ((), False, False, None, False, False),
    "WithStatement":        (("body", "object"),
                             False, False, actions._define_with, False, True),
    "SwitchStatement":      (("test", "cases"),
                             False, False, None, False, True),
    "ReturnStatement":      (("argument", ),
                             False, False, None, False, False),
    "ThrowStatement":       (("argument", ),
                             True, False, None, False, False),
    # The TryStatements are explecitly dynamic because I have no freakin idea
    # how to do static analysis on exception handling.
    "TryStatement":         (("block", "handler", "finalizer"),
                             True, False, None, False, True),
    "WhileStatement":       (("test", "body"),
                             False, False, None, False, True),
    "DoWhileStatement":     (("test", "body"),
                             False, False, None, False, True),
    "ForStatement":         (("init", "test", "update", "body"),
                             False, False, None, False, True),
    "ForInStatement":       (("left", "right", "body"),
                             False, False, None, False, True),

    "FunctionDeclaration":  (("body", ),
                             False, True, actions._define_function,
                             False, True),
    "VariableDeclaration":  (("declarations", ),
                             False, False, actions._define_var, False, False),

    "ThisExpression":       ((), False, False, actions._get_this, True, False),
    "ArrayExpression":      (("elements", ),
                             False, False, actions._define_array, True, False),
    "ObjectExpression":     (("properties", ),
                             False, False, actions._define_obj, True, False),
    "FunctionExpression":   (("body", ),
                             False, True, actions._func_expr,
                             True, True),
    "SequenceExpression":   (("expressions", ),
                             False, False, None, True, False),
    "UnaryExpression":      (("argument", ),
                             False, False, actions._expr_unary, True, False),
    "BinaryExpression":     (("left", "right"),
                             False, False, actions._expr_binary, True, False),
    "AssignmentExpression": (("left", "right"),
                             False, False, actions._expr_assignment, True,
                             False),
    "UpdateExpression":     (("argument", ),
                             False, False, None, True, False),
    "LogicalExpression":    (("left", "right"),
                             False, False, None, True, False),
    "ConditionalExpression":
                            (("test", "alternate", "consequent"),
                             False, False, None, True, False),
    "NewExpression":        (("constructor", "arguments"),
                             False, False, actions._new, True, False),
    "CallExpression":       (("callee", "arguments"),
                             False, False, actions._call_expression,
                             True, False),
    "MemberExpression":     (("object", "property"),
                             False, False, actions.trace_member, True, False),
    "YieldExpression":      (("argument"), True, False, None, True, False),
    "ComprehensionExpression":
                            (("body", "filter"),
                             False, False, None, True, False),
    "GeneratorExpression":  (("body", "filter"),
                             False, False, None, True, False),

    "ObjectPattern":        ((), False, False, None, False, False),
    "ArrayPattern":         ((), False, False, None, False, False),

    "SwitchCase":           (("test", "consequent"),
                             False, False, None, False, False),
    "CatchClause":          (("param", "guard", "body"),
                             True, False, None, True, False),
    "ComprehensionBlock":   (("left", "right"),
                             False, False, None, True, False),

    "Literal":              ((), False, False, actions._define_literal,
                             True, False),
    "Identifier":           ((), False, False, actions._ident, True, False),
    "GraphExpression":      ((), True, False, None, False, False),
    "GraphIndexExpression": ((), True, False, None, False, False),
    "UnaryOperator":        ((), False, False, None, True, False),
    "BinaryOperator":       ((), False, False, None, True, False),
    "LogicalOperator":      ((), False, False, None, True, False),
    "AssignmentOperator":   ((), False, False, None, True, False),
    "UpdateOperator":       ((), False, False, None, True, False)

    # E4X? What E4X? I have no idea what you're talking about. There's no E4X
    # here. Move along now, move along.

}
