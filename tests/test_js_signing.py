"""
Various tests related to validation for automated signing.
"""

from nose.tools import eq_

from .helper import RegexTestCase
from .js_helper import TestCase

from validator.testcases.regex.javascript import (PREFERENCE_ERROR_ID,
                                                  maybe_tuple)


class TestSearchService(TestCase, RegexTestCase):
    """Tests that warnings related to the search service trigger warnings."""

    def test_changes(self):
        """Tests that setting changes trigger warnings."""

        def test(obj, prop, stuff, warnings):
            self.setUp()
            self.run_script("""%s.%s%s;""" % (obj, prop, stuff))
            self.assert_failed(with_warnings=warnings)

        objs = ("Cc[''].getService(Ci.nsIBrowserSearchService)",
                'Services.search')

        for obj in objs:
            warnings = {'signing_severity': 'high',
                        'id': ('testcases_javascript_actions',
                               'search_service',
                               'changes')},

            for prop in 'currentEngine', 'defaultEngine':
                yield test, obj, prop, ' = foo', warnings

            warnings[0]['signing_severity'] = 'medium'

            for meth in ('addEngine', 'addEngineWithDetails',
                         'removeEngine', 'moveEngine'):
                yield test, obj, meth, '(foo, bar, baz)', warnings

    def test_registry_write(self):
        """Tests that Windows registry writes trigger warnings."""

        warnings = ({'id': ('testcases_javascript_actions',
                            'windows_registry', 'write'),
                     'signing_severity': 'medium'},
                    {'id': ('js', 'traverser', 'dangerous_global'),
                     'signing_severity': 'low'})

        def test(method):
            self.setUp()
            self.run_script("""
                Cc[""].createInstance(Ci.nsIWindowsRegKey).%s(foo, bar);
            """ % method)
            self.assert_failed(with_warnings=warnings)

        for method in ('create', 'createChild', 'writeBinaryValue',
                       'writeInt64Value', 'writeIntValue', 'writeStringValue'):
            yield test, method

    def test_evalInSandbox(self):
        """Tests that evalInSandbox causes signing warnings."""

        self.run_script("""
            Cu.evalInSandbox("foobar()", sandbox);
        """)
        self.assert_failed(with_warnings=[{'signing_severity': 'low'}])

    def test_pref_branches(self):
        """
        Tests that writes to potentially dangerous preferences are flagged.
        """

        def test(pref, severity):
            warnings = [
                {'message': 'Attempt to set a dangerous preference',
                 'signing_severity': severity}]

            self.setUp()
            self.run_script("""
                Services.prefs.setCharPref('%s', '42');
            """ % pref)
            self.assert_failed(with_warnings=warnings)

        PREFS = (('browser.newtab.url', 'high'),
                 ('browser.newtabpage.enabled', 'high'),
                 ('browser.search.defaultenginename', 'high'),
                 ('browser.startup.homepage', 'high'),
                 ('keyword.URL', 'high'),
                 ('keyword.enabled', 'high'),

                 ('app.update.*', 'high'),
                 ('browser.addon-watch.*', 'high'),
                 ('datareporting.', 'high'),
                 ('extensions.blocklist.*', 'high'),
                 ('extensions.getAddons.*', 'high'),
                 ('extensions.update.*', 'high'),

                 ('security.*', 'high'),

                 ('network.proxy.*', 'low'),
                 ('network.http.*', 'low'),
                 ('network.websocket.*', 'low'))

        for pref, severity in PREFS:
            yield test, pref, severity

    def test_pref_composed_branches(self):
        """
        Tests that preference warnings still happen when branches are composed
        via `getBranch`.
        """

        warnings = [
            {'message': 'Attempt to set a dangerous preference',
             'signing_severity': 'high'}]

        self.run_script("""
            Services.prefs.getBranch('browser.star')
                    .setCharPref('tup.homepage', 'http://evil.com');
        """)
        self.assert_failed(with_warnings=warnings)

        self.setUp()
        self.run_script("""
            let set = Services.prefs.getBranch('browser.star').setCharPref;
            set('tup.homepage', 'http://evil.com');
        """)
        self.assert_failed(with_warnings=warnings)

    def test_pref_literals_reported_once(self):
        """Tests that warnings for preference literals are reported only when
        necessary."""

        CALL_WARNING = {'id': ('testcases_javascript_actions',
                               '_call_expression', 'called_set_preference')}

        LITERAL_WARNING = {'id': PREFERENCE_ERROR_ID}

        SUMMARY = {'trivial': 0,
                   'low': 0,
                   'medium': 0,
                   'high': 1}

        # Literal without pref set call.
        self.run_script("""
            frob('browser.startup.homepage');
        """)

        self.assert_failed(with_warnings=[LITERAL_WARNING])
        eq_(len(self.err.warnings), 1)
        eq_(self.err.signing_summary, SUMMARY)

        # Literal with pref set call.
        for method in ('Services.prefs.setCharPref', 'Preferences.set'):
            self.setUp()
            self.run_script("""
                %s('browser.startup.homepage', '');
            """ % method)

            self.assert_failed(with_warnings=[CALL_WARNING])
            eq_(len(self.err.warnings), 1)
            eq_(self.err.signing_summary, SUMMARY)

        # Literal with pref set call on different line.
        self.setUp()
        self.run_script("""
            let bsh = 'browser.startup.homepage';
            Services.prefs.setCharPref(bsh, '');
        """)

        SUMMARY['high'] += 1
        self.assert_failed(with_warnings=[CALL_WARNING, LITERAL_WARNING])
        eq_(len(self.err.warnings), 2)
        eq_(self.err.signing_summary, SUMMARY)

    def test_get_preference_calls_ignored(self):
        """Tests that string literals provably used only to read, but not
        write, preferences do not cause warnings."""

        LITERAL_WARNING = {'id': PREFERENCE_ERROR_ID}

        # Literal without pref get or set call.
        self.run_script("""
            frob('browser.startup.homepage');
        """)

        self.assert_failed(with_warnings=[LITERAL_WARNING])
        eq_(len(self.err.warnings), 1)

        # Literal passed directly pref get call.
        for method in ('Services.prefs.getCharPref',
                       'Preferences.get'):
            self.setUp()
            self.run_script("""
                let thing = %s('browser.startup.homepage');
            """ % method)

            eq_(len(self.err.warnings), 0)

        # Literal passed indirectly pref get call.
        self.setUp()
        self.run_script("""
            let bsh = 'browser.sta' + 'rtup.homepage';
            let thing = Services.prefs.getCharPref(bsh);
        """)

        self.assert_failed(with_warnings=[LITERAL_WARNING])
        eq_(len(self.err.warnings), 1)

    def test_pref_help_added_to_bare_strings(self):
        """Test that a help messages about passing literals directly to
        APIs is added only to bare strings."""

        self.run_script("""
            'browser.startup.homepage';
            Preferences.set('browser.startup.homepage');
        """)

        warnings = self.err.warnings
        assert warnings[0]['id'] == PREFERENCE_ERROR_ID
        assert warnings[1]['id'] == ('testcases_javascript_actions',
                                     '_call_expression',
                                     'called_set_preference')

        # Check that descriptions and help are the same, except for
        # an added message in the bare string.
        for key in 'description', 'signing_help':
            val1 = maybe_tuple(warnings[0][key])
            val2 = maybe_tuple(warnings[1][key])

            eq_(val2, val1[:len(val2)])

            # And that the added message is what we expect.
            assert 'Preferences.get' in val1[-1]

    def test_profile_filenames(self):
        """
        Test that references to critical files in the user profile cause
        warnings.
        """

        warnings = [
            {'id': ('testcases_regex', 'string', 'profile_filenames'),
             'message': 'Reference to critical user profile data',
             'signing_severity': 'low'}]

        def fail(script):
            self.setUp()
            self.run_script(script)
            self.assert_failed(with_warnings=warnings)

        paths = (r'addons.json',
                 r'safebrowsing',
                 r'safebrowsing\\foo.bar',
                 r'safebrowsing/foo.bar')

        patterns = ("'%s'",
                    "'/%s'",
                    "'\\%s'")

        for path in paths:
            for pattern in patterns:
                yield fail, pattern % path

        yield fail, "'addons' + '.json'"

    def test_categories(self):
        """Tests that dangerous category names are flagged in JS strings."""

        warning = {'id': ('testcases_chromemanifest', 'test_resourcemodules',
                          'resource_modules'),
                   'message': 'Potentially dangerous category entry',
                   'signing_severity': 'medium',
                   'editors_only': True}

        self.run_script("'JavaScript-global-property'")
        self.assert_failed(with_warnings=[warning])

    def test_proxy_filter(self):
        """Tests that registering a proxy filter generates a warning."""

        warning = {'id': ('testcases_javascript_actions',
                          'predefinedentities', 'proxy_filter'),
                   'signing_severity': 'low',
                   'editors_only': True}

        self.run_script("""
            Cc[""].getService(Ci.nsIProtocolProxyService)
                 .registerFilter(foo, 0);
        """)
        self.assert_failed(with_warnings=[warning])

    def test_addon_install(self):
        """Tests attempts to install an add-on are flagged."""

        warning = {'id': ('js', 'traverser', 'dangerous_global'),
                   'editors_only': True,
                   'signing_severity': 'high'}

        def test(method):
            self.setUp()
            self.run_script("""
                AddonManager.%s(location, callback, plus, some, other, stuff);
            """ % method)
            self.assert_failed(with_warnings=[warning])

        for method in (u'getInstallForFile',
                       u'getInstallForURL'):
            yield test, method

    def test_addon_settings(self):
        """Tests that attempts to change add-on settings via the
        AddonManager API are flagged."""

        warning = {
            'description':
                'Changing this preference may have severe security '
                'implications, and is forbidden under most circumstances.',
            'editors_only': True,
            'signing_severity': 'high'}

        props = (u'autoUpdateDefault',
                 u'checkUpdateSecurity',
                 u'checkUpdateSecurityDefault',
                 u'updateEnabled')

        def test(prop):
            self.setUp()
            self.run_script('AddonManager.%s = false;' % prop)
            self.assert_failed(with_warnings=[warning])

        for prop in props:
            yield test, prop

    def test_ctypes(self):
        """Tests that usage of `ctypes` generates warnings."""

        self.run_script("""
            ctypes.open("libc.so.6");
        """)
        self.assert_failed(with_warnings=[
            {'id': ('js', 'traverser', 'dangerous_global'),
             'editors_only': True,
             'signing_severity': 'high'}])

    def test_nsIProcess(self):
        """Tests that usage of `nsIProcess` generates warnings."""

        self.run_script("""
            Cc[""].createInstance(Ci.nsIProcess);
        """)
        self.assert_failed(with_warnings=[
            {'id': ('js', 'traverser', 'dangerous_global'),
             'editors_only': True,
             'signing_severity': 'high'}])

    def test_eval(self):
        """Tests that usage of eval-related functions generates warnings."""

        functions = ('eval',
                     'Function',
                     'setTimeout',
                     'setInterval')

        warning = {'id': ('javascript', 'dangerous_global', 'eval'),
                   'signing_severity': 'high'}

        def test(func):
            self.setUp()
            self.run_script("%s('doEvilStuff()')" % func)
            self.assert_failed(with_warnings=[warning])

        for func in functions:
            yield test, func

    def test_cert_service(self):
        """Tests that changes to certificate trust leads to warnings."""

        interfaces = ('nsIX509CertDB',
                      'nsIX509CertDB2',
                      'nsIX509CertList',
                      'nsICertOverrideService')

        contracts = ('@mozilla.org/security/x509certdb;1',
                     '@mozilla.org/security/x509certlist;1',
                     '@mozilla.org/security/certoverride;1')

        warning = {'id': ('javascript', 'predefinedentities', 'cert_db'),
                   'editors_only': True,
                   'signing_severity': 'high'}

        def fail(script):
            self.setUp()
            self.run_script(script)
            self.assert_failed(with_warnings=[warning])

        for interface in interfaces:
            yield fail, "Cc[''].getService(Ci.%s)" % interface

        for contract in contracts:
            yield fail, "Cc['%s'].getService()" % contract

    def test_new_tab_page(self):
        """Tests that attempts to replace about:newtab are flagged."""

        patterns = (
            "if (foo == 'about:newtab') doStuff();",
            'if (bar === "about:blank") doStuff();',
            "if (baz==='about:newtab') doStuff();",
            "if ('about:newtab' == thing) doStuff();",
            '/^about:newtab$/.test(thing)',
            '/about:newtab/.test(thing)',
            "'@mozilla.org/network/protocol/about;1?what=newtab'")

        warning = {'signing_severity': 'low'}

        def fail(script):
            self.setUp()
            self.run_js_regex(script)
            self.assert_failed(with_warnings=[warning])

        for pattern in patterns:
            yield fail, pattern

    def test_script_creation(self):
        """Tests that creation of script tags generates warnings."""

        warning = {'id': ('testcases_javascript_instanceactions',
                          '_call_expression', 'called_createelement'),
                   'signing_severity': 'medium'}

        self.run_script("""
            doc.createElement("script");
        """)
        self.assert_failed(with_warnings=[warning])

    def test_event_attributes(self):
        """Tests that creation of event handler attributes is flagged."""

        warning = {'id': ('testcases_javascript_instanceactions',
                          'setAttribute', 'setting_on*'),
                   'signing_severity': 'medium'}

        self.run_script("""
            elem.setAttribute("onhover", "doStuff();" + with_stuff);
        """)
        self.assert_failed(with_warnings=[warning])

    def test_event_attributes_innerhtml(self):
        """Tests that creation of event handler attributes via innerHTML
        assignment is flagged."""

        warning = {'id': ('testcases_javascript_instancetypes',
                          'set_innerHTML', 'event_assignment'),
                   'signing_severity': 'medium'}

        self.run_script("""
            elem.innerHTML = '<a onhover="doEvilStuff()"></a>';
        """)
        self.assert_failed(with_warnings=[warning])

    def test_contentScript_dynamic_values(self):
        """Tests that dynamic values passed as contentScript properties
        trigger signing warnings."""

        warning = {'id': ('testcases_javascript_instanceproperties',
                          'contentScript', 'set_non_literal'),
                   'signing_severity': 'high'}

        self.run_script("""
            tab.attach({ contentScript: evil })
        """)
        self.assert_failed(with_warnings=[warning])

    def test_contentScript_static_values(self):
        """Tests that static, verifiable values passed as contentScripts
        trigger no warnings, but unsafe static values do."""

        # Test safe value.
        self.run_script("""
            tab.attach({ contentScript: "everythingIsCool()" })
        """)
        self.assert_silent()

        # Test unsafe value.
        warning = {'id': ('testcases_javascript_instanceactions',
                          '_call_expression', 'called_createelement'),
                   'signing_severity': 'medium'}

        self.setUp()
        self.run_script("""
            tab.attach({ contentScript: 'doc.createElement("script")' });
        """)
        self.assert_failed(with_warnings=[warning])
