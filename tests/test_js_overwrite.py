from js_helper import TestCase


class TestOverwrite(TestCase):
    """Test that JS variables can be properly overwritten."""

    def test_new_overwrite(self):
        """Tests that objects created with `new` can be overwritten."""

        self.run_script("""
        var x = new String();
        x += "asdf";
        x = "foo";
        """)
        self.assert_silent()

    def test_redefine_new_instance(self):
        """Test the redefinition of an instance of a global type."""

        self.run_script("""
        var foo = "asdf";
        var r = new RegEx(foo, "i");
        r = new RegExp(foo, "i");
        r = null;
        """)
        self.assert_silent()

    def test_property_members(self):
        """Tests that properties and members are treated fairly."""

        self.run_script("""
        var x = {"foo":"bar"};
        var y = x.foo;
        var z = x["foo"];
        """)
        self.assert_var_eq('y', 'bar')
        self.assert_var_eq('z', 'bar')

    def test_global_overwrite(self):
        """Tests that important objects cannot be overridden by JS."""

        def test(self, script, warnings=-1):
            self.setUp()
            self.run_script(script)
            if warnings > 0:
                self.assert_failed(with_warnings=True)
                assert len(self.err.warnings) == warnings
            elif warnings == -1:
                self.assert_failed()

        yield test, self, 'Number = "asdf"'
        yield test, self, 'Number.prototype = "foo"', 1
        yield test, self, 'Number.prototype.test = "foo"', 2
        yield test, self, 'Number.prototype["test"] = "foo"', 2
        yield test, self, 'x = Number.prototype; x.test = "foo"'

    def test_global_overwrite_bootstrapped(self):
        """Test that restartless add-ons don't get overwrite warnings."""

        def test(self, script):
            self.setUp()
            self.run_script(script, bootstrap=True)
            assert not any('global_overwrite' in m['id'] for
                           m in self.err.warnings)

        yield test, self, 'Number = "asdf"'
        yield test, self, 'Number.prototype = "foo"'
        yield test, self, 'Number.prototype.test = "foo"'
        yield test, self, 'Number.prototype["test"] = "foo"'
        yield test, self, 'x = Number.prototype; x.test = "foo"'

    def test_reduced_overwrite_messages(self):
        """
        Test that there are no messages for overwrites that occur in local
        scopes only.
        """

        self.run_script("""
        function foo() {
            let eval = "asdf";
            eval = 123;

            var Object = "foo";
            Object = "bar";
        }
        """)
        self.assert_silent()

    def test_reduced_overwrite_messages_block(self):
        """
        Test that there are no messages for overwrites that occur in block
        scope.
        """

        self.run_script("""
        if(true) {
            let eval = "asdf";
            eval = 123;

            var Object = "foo";
            Object = "bar";
        }
        """)
        self.assert_silent()

    def test_with_statement_pass(self):
        """Tests that 'with' statements work as intended."""

        self.run_script("""
        var x = {"foo":"bar"};
        with(x) {
            foo = "zap";
        }
        var z = x["foo"];
        """)
        self.assert_silent()
        self.assert_var_eq('z', 'zap')

    def test_with_statement_tested(self):
        """
        Assert that the contets of a with statement are still evaluated even if
        the context object is not available.
        """

        self.run_script("""
        with(foo.bar) { // These do not exist yet
            eval("evil");
        }
        """)
        self.assert_failed()

    def test_local_global_overwrite(self):
        """Test that a global assigned to a local variable can be overwritten."""

        self.run_script("""
        foo = String.prototype;
        foo = "bar";
        """)
        self.assert_silent()

    def test_overwrite_global(self):
        """Test that an overwritable global is overwritable."""

        self.run_script("""
        document.title = "This is something that isn't a global";
        """)
        self.assert_silent()

    def test_overwrite_readonly_false(self):
        """Test that globals with readonly set to false are overwritable."""

        self.run_script("""window.innerHeight = 123;""")
        self.assert_silent()

    def test_overwrite_selectedTab(self):
        """Test that gBrowser.selectedTab is overwriteable."""

        self.run_script("""gBrowser.selectedTab = 123;""")
        self.assert_silent()

    def test_constructors(self):
        """Test that the constructors cannot be overwritten."""
        def test(self, contsructor):
            self.setUp()
            self.run_script("""%s = "foo";""" % constructor)
            self.assert_failed(with_warnings=True)

        for constructor in ['Function', 'Object', 'String', 'Number', 'RegExp',
                            'File', 'Boolean', 'Array', 'Date']:
            yield test, self, constructor

