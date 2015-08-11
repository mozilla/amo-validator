import hashlib
import os
import re
from StringIO import StringIO
from zipfile import BadZipfile

from regex import run_regex_tests
from validator.constants import MAX_JS_THRESHOLD
from validator import decorator
from validator import submain as testendpoint_validator
from validator import unicodehelper
import validator.testcases.markup.markuptester as testendpoint_markup
import validator.testcases.markup.csstester as testendpoint_css
import validator.testcases.scripting as testendpoint_js
import validator.testcases.langpack as testendpoint_langpack
from validator.xpi import XPIManager
from validator.constants import (PACKAGE_LANGPACK, PACKAGE_SUBPACKAGE,
                                 PACKAGE_THEME)


FLAGGED_FILES = set(['.DS_Store', 'Thumbs.db'])
FLAGGED_EXTENSIONS = set(['.orig', '.old', '~'])
OSX_REGEX = re.compile('__MACOSX')

hash_library = {}
for hash_list in 'hashes.txt', 'static_hashes.txt':
    with open(os.path.join(os.path.dirname(__file__), hash_list)) as f:
        hash_library.update(s.strip().split(None, 1) for s in f)


@decorator.register_test(tier=1)
def test_xpcnativewrappers(err, xpi_package=None):
    """Tests the chrome.manifest file to ensure that it doesn't contain
    xpcnativewrappers objects."""

    # Don't even both with the test(s) if there's no chrome.manifest.
    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return None

    for triple in chrome.triples:
        # Test to make sure that the triple's subject is valid
        if triple['subject'] == 'xpcnativewrappers':
            err.warning(('testcases_content',
                         'test_xpcnativewrappers',
                         'found_in_chrome_manifest'),
                        'xpcnativewrappers not allowed in chrome.manifest',
                        'chrome.manifest files are not allowed to contain '
                        'xpcnativewrappers directives.',
                        filename=triple['filename'],
                        line=triple['line'],
                        context=triple['context'])


@decorator.register_test(tier=2)
def test_packed_packages(err, xpi_package=None):
    'Tests XPI and JAR files for naughty content.'

    processed_files = 0
    pretested_files = err.get_resource('pretested_files') or []

    scripts = set()
    chrome = err.get_resource('chrome.manifest_nopush')
    overlays = chrome.get_applicable_overlays(err) if chrome else set()

    marked_scripts = err.get_resource('marked_scripts')
    if not marked_scripts:
        marked_scripts = set()

    identified_files = err.metadata.setdefault('identified_files', {})

    # Iterate each item in the package.
    for name in xpi_package:

        # Warn for things like __MACOSX directories and .old files.
        if '__MACOSX' in name or name.split('/')[-1].startswith('.'):
            err.warning(
                err_id=('testcases_content', 'test_packed_packages',
                        'hidden_files'),
                warning='Hidden files and folders flagged',
                description='Hidden files and folders complicate the review '
                            'process and can contain sensitive information '
                            'about the system that generated the XPI. Please '
                            'modify the packaging process so that these files '
                            "aren't included.",
                filename=name)
            continue
        elif (any(name.endswith(ext) for ext in FLAGGED_EXTENSIONS) or
              name in FLAGGED_FILES):
            err.warning(
                err_id=('testcases_content', 'test_packaged_packages',
                        'flagged_files'),
                warning='Flagged filename found',
                description='Files were found that are either unnecessary '
                            'or have been included unintentionally. They '
                            'should be removed.',
                filename=name)
            continue

        # Skip the file if it's in the pre-tested files resource. This skips
        # things like Jetpack files.
        if name in pretested_files:
            continue

        # Read the file from the archive if possible.
        file_data = u''
        try:
            file_data = xpi_package.read(name)
        except KeyError:  # pragma: no cover
            pass

        if not err.for_appversions:
            hash = hashlib.sha256(file_data).hexdigest()
            identified = hash_library.get(hash)
            if identified is not None:
                identified_files[name] = {'path': identified}
                err.notice(
                    err_id=('testcases_content',
                            'test_packed_packages',
                            'blacklisted_js_library'),
                    notice='JS Library Detected',
                    description=('JavaScript libraries are discouraged for '
                                 'simple add-ons, but are generally '
                                 'accepted.',
                                 'File %r is a known JS library' % name),
                    filename=name)
                continue

        # Process the file.
        processed = False
        name_lower = name.lower()
        if name_lower.endswith(('.js', '.jsm')):
            # Add the scripts to a list to be processed later.
            scripts.add(name)
        elif name_lower.endswith(('.xul', '.xml', '.html', '.xhtml', '.xbl')):
            # Process markup files outside of _process_file so we can get
            # access to information about linked scripts and such.
            parser = testendpoint_markup.MarkupParser(err)
            parser.process(name, file_data,
                           xpi_package.info(name)['extension'])
            run_regex_tests(file_data, err, name)

            # Make sure the name is prefixed with a forward slash.
            prefixed_name = name if name.startswith('/') else '/%s' % name
            # Mark scripts as pollutable if this is an overlay file and there
            # are scripts to mark.
            if overlays and prefixed_name in overlays and parser.found_scripts:
                # Look up the chrome URL for the overlay
                reversed_chrome_url = chrome.reverse_lookup(err, name)
                for script in parser.found_scripts:
                    # Change the URL to an absolute URL.
                    script = _make_script_absolute(reversed_chrome_url, script)
                    if script:
                        # Mark the script as potentially pollutable.
                        marked_scripts.add(script)
                        err.save_resource('marked_scripts', marked_scripts)
                    else:
                        err.warning(
                            err_id=('testcases_content',
                                    'test_packed_packages',
                                    'invalid_chrome_url'),
                            warning='Invalid chrome URL',
                            description='The referenced chrome: URL '
                                        'could not be resolved to a '
                                        'script file.',
                            filename=name)

        else:
            # For all other files, simply throw it at _process_file.
            processed = _process_file(err, xpi_package, name, file_data,
                                      name_lower)
            # If the file is processed, it will return True. If the process
            # goes badly, it will return False. If the processing is skipped,
            # it returns None. We should respect that.
            if processed is None:
                continue

        # This is tested in test_langpack.py
        if err.detected_type == PACKAGE_LANGPACK and not processed:
            testendpoint_langpack.test_unsafe_html(err, name, file_data)

        # This aids in creating unit tests.
        processed_files += 1

    # If there aren't any scripts in the package, just skip the next few bits.
    if not scripts:
        return processed_files

    # Save the list of scripts, along with where to find them and the current
    # validation state.
    existing_scripts = err.get_resource('scripts')
    if not existing_scripts:
        existing_scripts = []
    existing_scripts.append({'scripts': scripts,
                             'package': xpi_package,
                             'state': err.package_stack[:]})
    err.save_resource('scripts', existing_scripts)

    return processed_files


@decorator.register_test(tier=3)
def test_packed_scripts(err, xpi_package):
    """
    Scripts must be tested separately from normal files to allow for markup
    files to mark scripts as being potentially polluting.
    """

    # This test doesn't apply to subpackages. We keep references to the
    # subpackage bundles so we can process everything at once in an unpushed
    # state.
    if err.is_nested_package:
        return

    scripts = err.get_resource('scripts')
    if not scripts:
        return

    total_scripts = sum(len(bundle['scripts']) for bundle in scripts)
    exhaustive = True
    if total_scripts > MAX_JS_THRESHOLD:
        err.warning(
            err_id=('testcases_content', 'packed_js', 'too_much_js'),
            warning='TOO MUCH JS FOR EXHAUSTIVE VALIDATION',
            description='There are too many JS files for the validator to '
                        'process sequentially. An editor must manually '
                        'review the JS in this add-on.')
        exhaustive = False

    # Get the chrome manifest in case there's information about pollution
    # exemptions.
    chrome = err.get_resource('chrome.manifest_nopush')
    marked_scripts = err.get_resource('marked_scripts')
    if not marked_scripts:
        marked_scripts = set()

    # Process all of the scripts that were found seperately from the rest of
    # the package contents.
    for script_bundle in scripts:
        package = script_bundle['package']

        # Set the error bundle's package state to what it was when we first
        # encountered the script file during the content tests.
        for archive in script_bundle['state']:
            err.push_state(archive)

        for script in script_bundle['scripts']:
            file_data = unicodehelper.decode(package.read(script))

            run_regex_tests(file_data, err, script, is_js=True)
            # If we're not running an exhaustive set of tests, skip the full JS
            # parse and traversal.
            if not exhaustive:
                continue

            if marked_scripts:
                reversed_script = chrome.reverse_lookup(script_bundle['state'],
                                                        script)
                # Run the standard script tests on the script, but mark the
                # script as pollutable if its chrome URL is marked as being so.
                testendpoint_js.test_js_file(
                    err, script, file_data,
                    pollutable=reversed_script in marked_scripts)
            else:
                # Run the standard script tests on the scripts.
                testendpoint_js.test_js_file(err, script, file_data)

        for i in range(len(script_bundle['state'])):
            err.pop_state()


@decorator.register_test(tier=2)
def test_signed_xpi(err, xpi_package):
    """Checks if XPI is signed.

    We don't want to specifically test for mozilla.* or zigbert.* filenames
    here, because the filenames could be just anything. Testing the presence of
    the manifest.mf file should be a good indicator that the file is signed."""
    if 'META-INF/manifest.mf' in xpi_package:
        err.warning(
            err_id=('testcases_content', 'signed_xpi'),
            warning='Package already signed',
            description='Add-ons which are already signed will be re-signed '
                        'when published on AMO. This will replace any '
                        'existing signatures on the add-on.')


def _process_file(err, xpi_package, name, file_data, name_lower,
                  pollutable=False):
    """Process a single file's content tests."""

    # If that item is a container file, unzip it and scan it.
    if name_lower.endswith('.jar'):
        # This is either a subpackage or a nested theme.
        is_subpackage = not err.get_resource('is_multipackage')
        # Unpack the package and load it up.
        package = StringIO(file_data)
        try:
            sub_xpi = XPIManager(package, mode='r', name=name,
                                 subpackage=is_subpackage)
        except BadZipfile:
            err.error(('testcases_content',
                       'test_packed_packages',
                       'jar_subpackage_corrupt'),
                      'Subpackage corrupt.',
                      'The subpackage appears to be corrupt, and could not '
                      'be opened.',
                      name)
            return None

        # Let the error bunder know we're in a sub-package.
        err.push_state(name)
        err.detected_type = (PACKAGE_SUBPACKAGE if is_subpackage else
                             PACKAGE_THEME)
        err.set_tier(1)
        supported_versions = (err.supported_versions.copy() if
                              err.supported_versions else
                              err.supported_versions)

        if is_subpackage:
            testendpoint_validator.test_inner_package(err, sub_xpi)
        else:
            testendpoint_validator.test_package(err, package, name)

        err.pop_state()
        err.set_tier(2)

        err.supported_versions = supported_versions

    elif name_lower.endswith('.xpi'):
        # It's not a subpackage, it's a nested extension. These are
        # found in multi-extension packages.

        # Unpack!
        package = StringIO(file_data)

        err.push_state(name_lower)
        err.set_tier(1)

        # There are no expected types for packages within a multi-
        # item package.
        testendpoint_validator.test_package(err, package, name)

        err.pop_state()
        err.set_tier(2)  # Reset to the current tier

    elif name_lower.endswith(('.css', '.js', '.jsm')):

        if not file_data:
            return None

        # Convert the file data to unicode
        file_data = unicodehelper.decode(file_data)
        is_js = name_lower.endswith(('.js', '.jsm'))

        if name_lower.endswith('.css'):
            testendpoint_css.test_css_file(err, name, file_data)

        elif is_js:
            testendpoint_js.test_js_file(err, name, file_data,
                                         pollutable=pollutable)

        run_regex_tests(file_data, err, name, is_js=is_js)

        return True

    else:
        if file_data:
            file_data = unicodehelper.decode(file_data)
            run_regex_tests(file_data, err, name, explicit=True)

    return False


def _make_script_absolute(xul_path, script):
    """Returns the absolute chrome URL for a script's URL."""

    # Ignore absolute URLs.
    if re.match(r'[a-z-]+:', script, re.IGNORECASE):
        return script

    if not xul_path:
        return

    if script.startswith('/'):
        xul_path_base = xul_path[9:]
        return 'chrome://%s%s' % (xul_path_base.split('/')[0], script)
    else:
        xul_path_split = xul_path.split('/')
        xul_path_split[-1] = script
        return '/'.join(xul_path_split)
