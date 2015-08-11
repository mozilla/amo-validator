from tests.js_helper import TestCase


class TestJSArrays(TestCase):
    """Test that arrays in the JS engine behave properly."""

    def test_object_overloading(self):
        self.run_script("""
        var x = [];
        x[1] = "asdf";
        x["asdf"] = "zxcv";
        var a = x[1],
            b = x.asdf;
        """)
        self.assert_var_eq('a', 'asdf')
        self.assert_var_eq('b', 'zxcv')

    def test_stringification(self):
        self.run_script("""
        var x = [4];
        var a = x * 3;
        """)
        self.assert_var_eq('a', 12)
