from validator.errorbundler import ErrorBundle
from validator.testcases import scripting


def _test(script):
    err = ErrorBundle()
    err.supported_versions = {}
    err.save_resource('em:bootstrap', 'true')
    scripting.test_js_file(err, 'foo', script)

    return err


def test_bootstrapped():
    'Performs a test on a JS file'

    methods = (
        ('nsICategoryManager', 'addCategoryEntry()'),
        ('nsIObserverService', 'addObserver()'),
        ('nsIResProtocolHandler', "setSubstitution('foo', 'bar')"),
        ('nsIStyleSheetService', 'loadAndRegisterSheet()'),
        ('nsIStringBundleService', 'createStringBundle()'),
        ('nsIWindowMediator', 'registerNotification()'),
        ('nsIWindowWatcher', 'addListener()'),
    )

    def test_wrap(js):
        assert _test(js).failed()

    for method in methods:
        yield test_wrap, 'Cc[""].getService(Ci.%s).%s;' % method

    yield test_wrap, 'XPCOMUtils.categoryManager.addCategoryEntry();'


def test_bootstrapped_pass():
    """Test that bootstrap-agnostic tests pass while boostrapping."""

    err = _test("""
        Cc[""]
          .getService(Ci.nsIResProtocolHandler)
          .setSubstitution("foo", null);
    """)
    print err.print_summary(verbose=True)
    assert not err.failed()


def test_bootstrapped_componentmanager():

    for method in ('autoRegister', 'registerFactory'):
        assert _test("""
            Components.manager
              .QueryInterface(Ci.nsIComponentRegistrar)
              .%s();
        """ % method).failed()
