from validator.errorbundler import ErrorBundle

from js_helper import TestCase

class TestE4X(TestCase):
    """
    Tests related to the E4X implementation in the JS engine.
    """

    def test_pass(self):
        """Test that E4X isn't immediately rejected."""
        self.run_script("""var x = <foo a={x}><bar /><{zap} /></foo>;""")
        self.assert_silent()

    def test_default_declaration(self):
        """
        Test that the E4X default declaration is tested as an expression.
        """
        self.run_script("""default xml namespace = eval("alert();");""");
        self.assert_failed(with_warnings=True)

    def test_xmlescape(self):
        """Test that XMLEscape nodes are evaluated."""
        self.run_script("""var x = <foo a={x}><bar /><{eval("X")} /></foo>;""")
        self.assert_failed(with_warnings=True)

