from mock import Mock
from nose.tools import eq_

from helper import MockXPI, TestCase
from js_helper import _do_real_test_raw as _do_test_raw
from validator.errorbundler import ErrorBundle
from validator.testcases.regex.base import RegexTestBase
from validator.testcases.regex.generic import FileRegexTest
from validator.testcases.regex.javascript import JSRegexTest, munge_filename
import validator.testcases.content


def test_valid():
    'Tests a valid string in a JS bit'
    assert not _do_test_raw("var x = 'network.foo';").failed()


def test_marionette_preferences_and_references_fail():
    'Tests that check for marionette. Added in bug 741812'

    _dtr = _do_test_raw
    assert _dtr("var x = 'marionette.defaultPrefs.port';").failed()
    assert _dtr("var x = 'marionette.defaultPrefs.enabled';").failed()
    assert _dtr("var x = 'marionette.force-local';").failed()
    assert _dtr("var x = '@mozilla.org/marionette;1';").failed()
    assert _dtr("var x = '{786a1369-dca5-4adc-8486-33d23c88010a}';").failed()
    assert _dtr('var x = MarionetteComponent;').failed()
    assert _dtr('var x = MarionetteServer;').failed()


def test_basic_regex_fail():
    'Tests that a simple Regex match causes a warning'

    assert _do_test_raw("var x = 'network.http.';").failed()
    assert _do_test_raw("var x = 'extensions.foo.update.url';").failed()
    assert _do_test_raw("var x = 'network.websocket.foobar';").failed()
    assert _do_test_raw("var x = 'browser.preferences.instantApply';").failed()
    assert _do_test_raw("var x = 'nglayout.debug.disable_xul_cache';").failed()

    err = ErrorBundle()
    err.supported_versions = {}
    validator.testcases.content._process_file(
        err, MockXPI(), 'foo.hbs',
        'All I wanna do is <%= interpolate %> to you',
        'foo.hbs')
    assert err.failed()


def test_dom_mutation_fail():
    """Test that DOM mutation events raise a warning."""

    assert not _do_test_raw('foo.DOMAttr = bar;').failed()
    assert _do_test_raw('foo.DOMAttrModified = bar;').failed()


def test_bug_548645():
    'Tests that banned entities are disallowed'

    results = _do_test_raw("""
    var y = newThread;
    var x = foo.newThread;
    var w = foo["newThread"];
    """)
    print results.print_summary(verbose=True)
    assert (len(results.errors) + len(results.warnings) +
            len(results.notices)) == 3


def test_processNextEvent_banned():
    """Test that processNextEvent is properly banned."""

    assert not _do_test_raw("""
    foo().processWhatever();
    var x = "processNextEvent";
    """).failed()

    assert _do_test_raw("""
    foo().processNextEvent();
    """).failed()

    assert _do_test_raw("""
    var x = "processNextEvent";
    foo[x]();
    """).failed()


def test_extension_manager_api():
    assert _do_test_raw("""
    Cc["@mozilla.org/extensions/manager;1"].getService();
    """).failed()

    assert _do_test_raw("""
    if (topic == "em-action-requested") true;
    """).failed()

    assert _do_test_raw("""
    thing.QueryInterface(Ci.nsIExtensionManager);
    """).failed()


def test_bug_652575():
    """Ensure that capability.policy gets flagged."""
    assert _do_test_raw("var x = 'capability.policy.';").failed()


def test_preference_extension_regex():
    """Test that preference extension regexes pick up the proper strings."""

    assert not (_do_test_raw('"chrome://mozapps/skin/extensions/update1.png"')
                .failed())
    assert _do_test_raw('"extensions.update.bar"').failed()


def test_template_escape():
    """Tests that the use of unsafe template escape sequences is flagged."""

    assert _do_test_raw('<%= foo %>').failed()
    assert _do_test_raw('{{{ foo }}}').failed()

    assert _do_test_raw("ng-bind-html-unsafe='foo'").failed()


def test_servicessync():
    """
    Test that instances of `resource://services-sync` are flagged due to their
    volatile nature.
    """

    err = _do_test_raw("""
    var r = "resource://services-sync";
    """)
    assert err.failed()
    assert err.warnings
    assert not any(val for k, val in err.compat_summary.items())


def test_mouseevents():
    """Test that mouse events are properly handled."""

    err = _do_test_raw("window.addEventListener('mousemove', func);")
    assert err.warnings


def test_munge_filename():
    """Tests that the munge_filename function has the expected results."""

    eq_(munge_filename('foo.bar'), r'foo\.bar'),
    eq_(munge_filename('foo.bar/*'), r'foo\.bar(?:[/\\].*)?')


class TestRegexTest(TestCase):
    def test_process_key(self):
        """Test that the process_key method behaves as expected."""

        key = RegexTestBase(()).process_key

        # Test that plain strings stay unmolested
        string = r'foo\*+?.|{}[]()^$'
        eq_(key(string), string)

        # Test that tuples are converted to expected full-string regexps
        eq_(key(('foo',)), r'^(?:foo)$')

        eq_(key(('foo', 'bar')), r'^(?:foo|bar)$')

        eq_(key((r'foo\*+?.|{}[]()^$', 'bar')),
            r'^(?:foo\\\*\+\?\.\|\{\}\[\]\(\)\^\$|bar)$')

    def test_glomming(self):
        """Test that multiple regular expressions are glommed together
        properly."""

        def expect(keys, val):
            eq_(RegexTestBase(tuple((key, {}) for key in keys)).patterns,
                val)

        expect(['foo'], {'test_0': 'foo'})

        expect([r'foo\|\**'], {'test_0': 'foo\|\**'})

        expect(('foo', 'bar'), {'test_0': 'foo', 'test_1': 'bar'})

        expect((r'foo\|\**', 'bar'), {'test_0': 'foo\|\**', 'test_1': 'bar'})

    def test_multiple_warnings(self):
        """Test that multiple warnings are emitted where appropriate."""

        traverser = Mock()

        inst = JSRegexTest((('f.o', {'warning': 'foo'}),
                            ('b.r', {'warning': 'bar'})))

        eq_(inst.patterns, {'test_0': 'f.o', 'test_1': 'b.r'})

        inst.test('foo bar baz fxo', traverser=traverser)

        calls = traverser.report.call_args_list
        eq_([args[0][1]['warning'] for args in calls],
            ['foo', 'bar', 'foo'])

    def test_format(self):
        """Test that certain properties are treated as format strings,
        and passed the correct match text."""

        tester = RegexTestBase((
            (r'fo+o-b.r', {'warning': 'Wa-{match}-ning',
                           'description': 'Des-{match}-cription',
                           'signing_help': ('Sign-{match}-ing',
                                            'he-{match}-lp')}),
        ))

        tester.test('Hello foooooo-ber there.', err=self.err)

        self.assert_failed(with_warnings=[
            {'message': 'Wa-foooooo-ber-ning',
             'description': 'Des-foooooo-ber-cription',
             'signing_help': ('Sign-foooooo-ber-ing', 'he-foooooo-ber-lp')},
        ])

    def test_err_id(self):
        """Test that an appropriate error ID is added for a test pattern."""

        tester = RegexTestBase((
            (r'Y.. k.ll.d my f.th.r.', {'warning': 'Prepare to'}),
        ))

        tester.test('Montoya. You killed my father.', err=self.err)

        self.assert_failed(with_warnings=[
            {'message': 'Prepare to',
             'id': ('testcases_regex', 'basic', 'Y.. k.ll.d my f.th.r.')},
        ])


class TestFileRegexTest(TestCase):
    def test_filters(self):
        """Test that various filters work as expected."""

        FOO_FILTERS = (
            lambda kw: 'foo' in kw['document'],
            {'document': 'foo'},
        )
        JS_FILTERS = (
            {'extension': ('.json', '.js')},
            {'is_javascript': True},
            {'filename': r'\.js$'},
        )
        MULTI_FILTERS = (
            {'document': 'foo', 'is_javascript': True},
        )

        all_filters = FOO_FILTERS + JS_FILTERS + MULTI_FILTERS

        # Make a tester and base string which will match a pattern for each of
        # our filters.
        filter_dict = {'%02d' % i: filter_
                       for i, filter_ in enumerate(all_filters)}
        base_string = ' '.join(sorted(filter_dict.keys()))

        tester = FileRegexTest((key, {'err_id': (key,), 'warning': 'Foo.',
                                      'filter': filter_})
                               for key, filter_ in filter_dict.iteritems())

        def matching_filters(string, **kw):
            """Run our tester with the given string fragment and keyword
            arguments, and return a tuple of all matching filters."""

            err = ErrorBundle()
            tester.test('%s %s' % (string, base_string), err=err, **kw)
            return tuple(filter_dict[msg['id'][0]] for msg in err.warnings)

        # All filters should match a JavaScript file containing the string
        # 'foo'.
        eq_(matching_filters('foo', filename='foo.js'), all_filters)

        # An arbitrary, non-JS file containing the string 'foo' should match
        # just the first set.
        eq_(matching_filters('foo', filename='foo.bar'), FOO_FILTERS)

        # And a .js file not containing the string 'foo' should match just the
        # second set.
        eq_(matching_filters('', filename='foo.js'), JS_FILTERS)

        # Finally, an arbitrary, non-JS file, not containing the string 'foo',
        # should match none.
        eq_(matching_filters('', filename='foo.bar'), ())

    def test_add_context(self):
        """Test that context is added to output as appropriate."""

        tester = FileRegexTest((
            (r'foo', {'warning': 'Hello.'}),
        ))

        document = """
            Hello.
            bar foo baz
            World.
        """

        FILENAME = 'gorm.js'

        tester.test(document, err=self.err, filename=FILENAME)

        self.assert_failed(with_warnings=[
            {'message': 'Hello.',
             'file': FILENAME,
             'line': 3,
             'context': ('Hello.', 'bar foo baz', 'World.')},
        ])
