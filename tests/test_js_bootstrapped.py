import pytest

from validator.errorbundler import ErrorBundle
from validator.testcases import scripting


scripting.traverser.DEBUG = True


def _test(script):
    err = ErrorBundle()
    err.supported_versions = {}
    err.save_resource('em:bootstrap', 'true')
    scripting.test_js_file(err, 'foo', script)

    return err


@pytest.mark.parametrize("test_input", [
    ('nsICategoryManager', 'addCategoryEntry()'),
    ('nsIObserverService', 'addObserver()'),
    ('nsIResProtocolHandler', "setSubstitution('foo', 'bar')"),
    ('nsIStyleSheetService', 'loadAndRegisterSheet()'),
    ('nsIStringBundleService', 'createStringBundle()'),
    ('nsIWindowMediator', 'registerNotification()'),
    ('nsIWindowWatcher', 'addListener()'),
])
def test_bootstrapped(test_input):
    'Performs a test on a JS file'
    test = 'Cc[""].getService(Ci.%s).%s;' % test_input
    assert _test(test).failed()
    assert _test('XPCOMUtils.categoryManager.addCategoryEntry();').failed()


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
