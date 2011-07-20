import fnmatch
import hashlib
import re
from StringIO import StringIO

from regex import run_regex_tests
from validator.contextgenerator import ContextGenerator
from validator import decorator
from validator import submain as testendpoint_validator
from validator import unicodehelper
import validator.testcases.markup.markuptester as testendpoint_markup
import validator.testcases.markup.csstester as testendpoint_css
import validator.testcases.scripting as testendpoint_js
import validator.testcases.langpack as testendpoint_langpack
from validator.xpi import XPIManager
from validator.constants import *
from validator.textfilter import is_standard_ascii


PASSWORD_REGEX = re.compile("password", re.I)
OSX_REGEX = re.compile("__MACOSX")

@decorator.register_test(tier=1)
def test_xpcnativewrappers(err, xpi_package=None):
    """Tests the chrome.manifest file to ensure that it doesn't contain
    xpcnativewrappers objects."""

    # Don't even both with the test(s) if there's no chrome.manifest.
    chrome = err.get_resource("chrome.manifest")
    if not chrome:
        return None

    for triple in chrome.triples:
        # Test to make sure that the triple's subject is valid
        if triple["subject"] == "xpcnativewrappers":
            err.warning(("testcases_content",
                         "test_xpcnativewrappers",
                         "found_in_chrome_manifest"),
                        "xpcnativewrappers not allowed in chrome.manifest",
                        "chrome.manifest files are not allowed to contain "
                        "xpcnativewrappers directives.",
                        "chrome.manifest",
                        line=triple["line"],
                        context=chrome.context)


@decorator.register_test(tier=2)
def test_packed_packages(err, xpi_package=None):
    "Tests XPI and JAR files for naughty content."

    processed_files = 0
    pretested_files = err.get_resource("pretested_files") or []

    with open(os.path.join(os.path.dirname(__file__),
              "hashes.txt")) as f:
        hash_blacklist = [x[:-1] for x in f]

    with open(os.path.join(os.path.dirname(__file__),
              "whitelist_hashes.txt")) as f:
        hash_whitelist = [x[:-1] for x in f]

    # Iterate each item in the package.
    for name in xpi_package:
        if (OSX_REGEX.search(name) or
            name.startswith(".") or
            name.split("/")[-1].startswith(".")):
            err.warning(
                err_id=("testcases_content", "test_packed_packages",
                        "hidden_files"),
                warning="Hidden files and folders flagged",
                description="Hidden files and folders difficult the review "
                            "process and can contain sensitive information "
                            "about the system that generated the XPI. Please "
                            "modify the packaging process so that these files "
                            "aren't included.",
                filename=name)
            continue

        if name in pretested_files:
            continue

        try:
            file_data = xpi_package.read(name)
        except KeyError:  # pragma: no cover
            pass

        # Skip over whitelisted and blacklisted hashes
        hash = hashlib.sha1(file_data).hexdigest()
        if hash in hash_whitelist:
            continue
        elif hash in hash_blacklist:
            err.notice(("testcases_content",
                        "test_packed_packages",
                        "blacklisted_js_library"),
                       "JS Library Detected",
                       ["JavaScript libraries are discouraged for simple "
                        "add-ons, but are generally accepted.",
                        "File '%s' is a known JS library" % name],
                       name)
            continue

        # Process the file.
        processed = _process_file(err, xpi_package, name, file_data)
        if processed is None:
            continue

        # This is tested in test_langpack.py
        if err.detected_type == PACKAGE_LANGPACK and not processed:
            testendpoint_langpack.test_unsafe_html(err, name, file_data)

        # This aids in creating unit tests.
        processed_files += 1

    return processed_files


def _process_file(err, xpi_package, name, file_data):
    """Process a single file's content tests."""
    name_lower = name.lower()

    # If that item is a container file, unzip it and scan it.
    if name_lower.endswith(".jar"):
        # This is either a subpackage or a nested theme.
        is_subpackage = not err.get_resource("is_multipackage")
        # Unpack the package and load it up.
        package = StringIO(file_data)
        try:
            sub_xpi = XPIManager(package, mode="r", name=name,
                                 subpackage=is_subpackage)
        except:
            err.error(("testcases_content",
                       "test_packed_packages",
                       "jar_subpackage_corrupt"),
                      "Subpackage corrupt.",
                      "The subpackage could not be opened due to issues "
                      "with corruption. Ensure that the file is valid.",
                      name)
            return None

        # Let the error bunder know we're in a sub-package.
        err.push_state(name.lower())
        err.set_type(PACKAGE_SUBPACKAGE if
                     is_subpackage else
                     PACKAGE_THEME)
        err.set_tier(1)
        supported_versions = err.supported_versions

        if is_subpackage:
            testendpoint_validator.test_inner_package(err, sub_xpi)
        else:
            testendpoint_validator.test_package(err, package, name)

        package.close()
        err.pop_state()
        err.set_tier(2)

        err.supported_versions = supported_versions

    elif name_lower.endswith(".xpi"):
        # It's not a subpackage, it's a nested extension. These are
        # found in multi-extension packages.

        # Unpack!
        package = StringIO(file_data)

        err.push_state(name_lower)
        err.set_tier(1)

        # There are no expected types for packages within a multi-
        # item package.
        testendpoint_validator.test_package(err, package, name)

        package.close()
        err.pop_state()
        err.set_tier(2)  # Reset to the current tier

    elif name_lower.endswith((".xul", ".xml", ".html", ".xhtml", ".xbl")):

        parser = testendpoint_markup.MarkupParser(err)
        parser.process(name, file_data,
                       xpi_package.info(name)["extension"])

        run_regex_tests(file_data, err, name)
        return True

    elif name_lower.endswith((".css", ".js", ".jsm")):

        if not file_data:
            return None

        # Convert the file data to unicode
        file_data = unicodehelper.decode(file_data)

        if name_lower.endswith(".css"):
            testendpoint_css.test_css_file(err, name, file_data)

        elif name_lower.endswith((".js", ".jsm")):
            # Test for "password" in defaults/preferences files; bug 647109
            if fnmatch.fnmatch(name, "defaults/preferences/*.js"):
                match = PASSWORD_REGEX.search(file_data)
                if match:
                    context = ContextGenerator(file_data)
                    err.warning(
                        err_id=("testcases_content",
                                "test_packed_packages",
                                "password_in_js"),
                        warning="Passwords may be stored in defaults/"
                                "preferences JS files",
                        description="Storing passwords in the preferences "
                                    "is insecure and the Login Manager "
                                    "should be used instead.",
                        filename=name,
                        line=context.get_line(match.start()),
                        context=context)

            testendpoint_js.test_js_file(err, name, file_data)

        run_regex_tests(file_data, err, name)

    return False

