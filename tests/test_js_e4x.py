from validator.errorbundler import ErrorBundle

from js_helper import TestCase

class TestE4X(TestCase):
    """
    Tests related to the E4X implementation in the JS engine.
    """

    def run_script(self, script):
        output = super(TestE4X, self).run_script(script)
        self.err.warnings = filter(
            lambda w: w["id"][-1] == "e4x", self.err.warnings)
        return output

    def test_pass(self):
        """Test that E4X isn't immediately rejected."""
        self.run_script("""var x = <foo a={x}><bar /><{zap} /></foo>;""")

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

    def test_xmlname_string(self):
        """Test that XMLName nodes with a string "contents" works."""
        self.run_script("""
        let reportData =
        	<report>
        		<adblock-plus version={Utils.addonVersion}
                    build={Utils.addonBuild} locale={Utils.appLocale}/>
        		<application name={Utils.appInfo.name}
                    vendor={Utils.appInfo.vendor}
                    version={Utils.appInfo.version}
                    userAgent={window.navigator.userAgent}/>
        		<platform name="Gecko"
                    version={Utils.appInfo.platformVersion}
                    build={Utils.appInfo.platformBuildID}/>
        		<options>
        			<option id="enabled">{Prefs.enabled}</option>
        			<option id="objecttabs">{Prefs.frameobjects}</option>
        			<option id="collapse">{!Prefs.fastcollapse}</option>
        		</options>
        		<window/>
        		<requests/>
        		<filters/>
        		<subscriptions/>
        		<errors/>
        	</report>;
        """)
        self.assert_failed(with_warnings=True)

    def test_xmlattributeselector(self):
        """Test that XMLAttributeSelectors don't throw tracebacks."""
        self.run_script("""
        var x = <foo zip="zap"><bar /></foo>;
        var y = x.@zip;
        """)
        self.assert_failed(with_warnings=True)

    def test_double_colon(self):
        """
        Test that assignmnts with a double colon on an E4X object don't cause a
        traceback.
        """
        self.run_script("""
        var req = <nsMessages:GetItem xmlns:nsMessages={nsMessages}
                      xmlns:nsTypes={nsTypes}/>;
        req::asdf.oijaewr::aasdf = "foo";
        """)
        self.assert_failed(with_warnings=True)

    def test_all_deprecated(self):
        """Test that all of the node types are flagged."""
        def wrap(line):
            print line
            self.setUp()
            self.run_script(line)
            self.assert_failed(with_warnings=True)

        yield wrap, 'var x = <![CDATA[Foo.]]>;'
        yield wrap, 'var x = <>Bar.</>;'
        yield wrap, 'var x = XML("<foo/>");'
        yield wrap, 'var x = QName("thing", "stuff");'
        yield wrap, 'var x = Namespace("foo", "bar");'
        yield wrap, 'var x = frag..foo;'
        yield wrap, 'var x = thing.@foo;'
        yield wrap, 'var x = thing.ns::thing;'
