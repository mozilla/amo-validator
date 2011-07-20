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
    "EmptyStatement":       ((), False, None, False, False),
    "DebuggerStatement":    ((), False, None, False, False),

    "Program":              (("body", ), True, None, False, True),
    "BlockStatement":       (("body", ), False, None, False, True),
    "ExpressionStatement":  (("expression", ),
                             False, actions._expression, True, False),
    "IfStatement":          (("test", "alternate", "consequent"),
                             False, None, True, True),
    "LabeledStatement":     (("body", ),False, None, False, False),
    "BreakStatement":       ((), False, None, False, False),
    "ContinueStatement":    ((), False, None, False, False),
    "WithStatement":        (("body", "object"),
                             False, actions._define_with, False, True),
    "SwitchStatement":      (("test", "cases"),
                             False, None, False, True),
    "ReturnStatement":      (("argument", ),
                             False, None, False, False),
    "ThrowStatement":       (("argument", ),
                             False, None, False, False),
    "TryStatement":         (("block", "handler", "finalizer"),
                             False, None, False, True),
    "WhileStatement":       (("test", "body"),
                             False, None, False, True),
    "DoWhileStatement":     (("test", "body"),
                             False, None, False, True),
    "ForStatement":         (("init", "test", "update", "body"),
                             False, None, False, True),
    "ForInStatement":       (("left", "right", "body"),
                             False, None, False, True),

    "FunctionDeclaration":  (("body", ),
                             True, actions._define_function, False, True),
    "VariableDeclaration":  (("declarations", ),
                             False, actions._define_var, False, False),

    "ThisExpression":       ((), False, actions._get_this, True, False),
    "ArrayExpression":      (("elements", ),
                             False, actions._define_array, True, False),
    "ObjectExpression":     (("properties", ),
                             False, actions._define_obj, True, False),
    "FunctionExpression":   (("body", ),
                             True, actions._func_expr, True, True),
    "SequenceExpression":   (("expressions", ),
                             False, None, True, False),
    "UnaryExpression":      (("argument", ),
                             False, actions._expr_unary, True, False),
    "BinaryExpression":     (("left", "right"),
                             False, actions._expr_binary, True, False),
    "AssignmentExpression": (("left", "right"),
                             False, actions._expr_assignment, True, False),
    "UpdateExpression":     (("argument", ),
                             False, None, True, False),
    "LogicalExpression":    (("left", "right"),
                             False, None, True, False),
    "ConditionalExpression":
                            (("test", "alternate", "consequent"),
                             False, None, True, False),
    "NewExpression":        (("constructor", "arguments"),
                             False, actions._new, True, False),
    "CallExpression":       (("callee", "arguments"),
                             False, actions._call_expression, True, False),
    "MemberExpression":     (("object", "property"),
                             False, actions.trace_member, True, False),
    "YieldExpression":      (("argument"), False, None, True, False),
    "ComprehensionExpression":
                            (("body", "filter"),
                             False, None, True, False),
    "GeneratorExpression":  (("body", "filter"),
                             False, None, True, False),

    "ObjectPattern":        ((), False, None, False, False),
    "ArrayPattern":         ((), False, None, False, False),

    "SwitchCase":           (("test", "consequent"),
                             False, None, False, False),
    "CatchClause":          (("param", "guard", "body"),
                             False, None, True, False),
    "ComprehensionBlock":   (("left", "right"),
                             False, None, True, False),

    "Literal":              ((), False, actions._define_literal,
                             True, False),
    "Identifier":           ((), False, actions._ident, True, False),
    "GraphExpression":      ((), False, None, False, False),
    "GraphIndexExpression": ((), False, None, False, False),
    "UnaryOperator":        ((), False, None, True, False),
    "BinaryOperator":       ((), False, None, True, False),
    "LogicalOperator":      ((), False, None, True, False),
    "AssignmentOperator":   ((), False, None, True, False),
    "UpdateOperator":       ((), False, None, True, False)

    # E4X? What E4X? I have no idea what you're talking about. There's no E4X
    # here. Move along now, move along.

}
