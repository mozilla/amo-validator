from tests.js_helper import TestCase


class TestFunctionTraversal(TestCase):
    """
    Consider the following tree:

    - body
      |-function a()
      | |- foo
      | |- bar
      |-zip
      |-function b()
      | |-abc
      | |-def
      |-zap

    In the old traversal technique, it would be evaluated in the order:

        body a() foo bar zip b() abc def zap

    If the tree is considered as a graph, this would be prefix notation
    traversal.

    This is not optimal, however, as JS commonly uses callbacks which are set
    up before delegation code. The new traversal technique should access nodes
    in the following order:

        body zip zap a() foo bar b() abc def

    If the tree is considered a graph, this would be a custom prefix notation
    traversal where all non-function nodes are traversed before all function
    nodes.
    """

    def test_function_declaration_order(self):
        """Test that function declarations happen in the right time."""

        self.run_script("""
        foo = "first";
        function test() {
            foo = "second";
        }
        bar = foo;
        """)
        self.assert_var_eq("bar", "first")
        self.assert_var_eq("foo", "second")

    def test_function_expression_order(self):
        """Test that function expressions happen in the right time."""

        self.run_script("""
        foo = "first"
        var x = function() {
            foo = "second";
        }
        bar = foo;
        """)
        self.assert_var_eq("bar", "first")
        self.assert_var_eq("foo", "second")

    def test_nested_functions(self):
        """Test that nested functions are considered in the right order."""

        self.run_script("""
        foo = "first"
        function test() {
            function a() {foo = "second"}
            foo = "third";
        }
        """)
        self.assert_var_eq("foo", "second")

