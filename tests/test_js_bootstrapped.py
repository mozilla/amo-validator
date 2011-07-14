from validator.errorbundler import ErrorBundle
from validator.testcases import scripting

scripting.traverser.DEBUG = True

def _test(script):
    err = ErrorBundle()
    err.supported_versions = {}
    err.save_resource("em:bootstrap", "true")
    scripting.test_js_file(err, "foo", script)

    return err


def test_bootstrapped():
    "Performs a test on a JS file"

    methods = (
        ("nsICategoryManager", "addCategoryEntry()"),
        ("nsIObserverService", "addObserver()"),
        ("nsIResProtocolHandler", "setSubstitution('foo', 'bar')"),
        ("nsIStyleSheetService", "loadAndRegisterSheet()"),
        ("nsIStringBundleService", "createStringBundle()"),
        ("nsIWindowMediator", "registerNotification()"),
        ("nsIWindowWatcher", "addListener()"),
    )

    for method in methods:
        assert _test("""
            Components.classes[""]
                      .getService(Components.interfaces.%s)
                      .%s;
        """ % method).failed()

    assert not _test("""
        Components.classes[""]
                  .getService(Components.interfaces.nsIResProtocolHandler)
                  .setSubstitution("foo", null);
    """).failed()

def test_bootstrapped_componentmanager():

    for method in ('autoRegister', 'registerFactory'):
        assert _test("""
            Components.manager.QueryInterface(Components.interfaces.nsIComponentRegistrar)
                      .%s();
        """ % method).failed()

