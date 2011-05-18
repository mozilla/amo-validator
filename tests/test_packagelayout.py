import validator.testcases.packagelayout as packagelayout
from validator.errorbundler import ErrorBundle
from helper import _do_test


def test_npapi():
    "Tests that NPAPI plugins are flagged within extensions"

    err = ErrorBundle()
    # It is assumed that this only runs for extension tests; this is specified
    # in the decorator.
    packagelayout.test_npapi(err, {})
    assert not err.failed()
    packagelayout.test_npapi(err, {"plugins/foo.bar":False})
    assert not err.failed()
    packagelayout.test_npapi(err, {"plugins/foo.dll":False})
    assert err.failed()


def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""

    err = _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_extension"]
    assert err.warnings
    assert all(m["compatibility_type"] == "error" for
               m in
               err.warnings)

def test_blacklisted_magic_numbers():
    "Tests that blacklisted magic numbers are banned"

    err = _do_test("tests/resources/packagelayout/magic_number.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_content"]
    assert err.warnings
    assert all(m["compatibility_type"] == "error" for
               m in
               err.warnings)


# These functions will test the code with manually constructed packages
# that contain valid or failing versions of the specified package. The
# remaining tests will simply emulate this behaviour (since it was
# successfully tested with these functions).

def test_theme_passing():
    "Tests the layout of a proper theme"

    _do_test("tests/resources/packagelayout/theme.jar",
             packagelayout.test_theme_layout,
             False)

def test_extra_unimportant():
    """Tests the layout of a theme that contains an unimportant but
    extra directory."""

    _do_test("tests/resources/packagelayout/theme_extra_unimportant.jar",
             packagelayout.test_theme_layout,
             False)

def _do_simulated_test(function, structure, failure=False, ff4=False):
    """"Performs a test on a function or set of functions without
    generating a full package."""

    dict_structure = {"__MACOSX/foo.bar": True}
    for item in structure:
        dict_structure[item] = True

    err = ErrorBundle(None, True)
    err.save_resource("ff4", ff4)
    function(err, dict_structure, None)

    err.print_summary(True)

    if failure:
        assert err.failed()
    else:
        assert not err.failed()

    return err

def test_langpack_max():
    """Tests the package layout module out on a simulated language pack
    containing the largest number of possible elements."""

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ["install.rdf",
                        "chrome/foo.jar",
                        "chrome.manifest",
                        "chrome/bar.test.jar",
                        "foo.manifest",
                        "bar.rdf",
                        "abc.dtd",
                        "def.jar",
                        "chrome/asdf.properties",
                        "chrome/asdf.xhtml",
                        "chrome/asdf.css"])

def test_dict_max():
    """Tests the package layout module out on a simulated dictionary
    containing the largest number of possible elements."""

    _do_simulated_test(packagelayout.test_dictionary_layout,
                       ["install.rdf",
                        "dictionaries/foo.aff",
                        "dictionaries/bar.test.dic",
                        "install.js",
                        "dictionaries/foo.aff",
                        "dictionaries/bar.test.dic",
                        "chrome.manifest",
                        "chrome/whatever.jar"])

def test_unknown_file():
    """Tests that the unknown file detection function is working."""

    # We test against langpack because it is incredibly strict in its
    # file format.

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ["install.rdf",
                        "chrome/foo.jar",
                        "chrome.manifest",
                        "chromelist.txt"])

def test_disallowed_file():
    """Tests that outright improper files are blocked."""

    # We test against langpack because it is incredibly strict in its
    # file format.

    _do_simulated_test(packagelayout.test_langpack_layout,
                       ["install.rdf",
                        "chrome/foo.jar",
                        "chrome.manifest",
                        "foo.bar"],
                       True)


def test_extra_obsolete():
    """Tests that unnecessary, obsolete files are detected."""

    err = ErrorBundle(None, True)

    # Tests that chromelist.txt is treated (with and without slashes in
    # the path) as an obsolete file.
    assert not packagelayout.test_unknown_file(err, "x//whatever.txt")
    assert not packagelayout.test_unknown_file(err, "whatever.txt")
    assert packagelayout.test_unknown_file(err, "x//chromelist.txt")
    assert packagelayout.test_unknown_file(err, "chromelist.txt")

    assert not err.failed()


def test_has_installrdfs():
    """Tests that install.rdf files are present and that subpackage
    rules are respected."""

    # Test package to make sure has_install_rdf is set to True.
    assert not _do_installrdfs(packagelayout.test_layout_all)
    assert _do_installrdfs(packagelayout.test_layout_all, False)

    mock_xpi_subpack = MockXPIAll(True)

    # Makes sure the above test is ignored if the package is a
    # subpackage.
    assert not _do_installrdfs(packagelayout.test_layout_all,
                               False,
                               mock_xpi_subpack)
    assert not _do_installrdfs(packagelayout.test_layout_all,
                               True,
                               mock_xpi_subpack)



class MockXPIAll:
    "Simulates an XPI package manager object"

    def __init__(self, subpackage=False):
        self.subpackage = subpackage


def _do_installrdfs(function, has_install_rdf=True, xpi=None):
    "Helps to test that install.rdf files are present"

    err = ErrorBundle(None, True)

    if xpi is None:
        xpi = MockXPIAll()

    if has_install_rdf:
        content = {"install.rdf" : True}
        err.save_resource("has_install_rdf", True)
    else:
        content = {}
    function(err, content, xpi)

    return err.failed()


