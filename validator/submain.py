import json
import os
import signal
import sys
from zipfile import BadZipfile
from zlib import error as zlib_error

from defusedxml.common import DefusedXmlException

import validator
from validator import decorator
from validator.chromemanifest import ChromeManifest
from validator.constants import MDN_DOC
from validator.json_parser import ManifestJsonParser
from validator.opensearch import detect_opensearch
from validator.rdf import RDFException, RDFParser
from validator.typedetection import detect_type
from validator.xpi import XPIManager

from constants import (PACKAGE_ANY, PACKAGE_EXTENSION, PACKAGE_SEARCHPROV,
                       PACKAGE_SUBPACKAGE, PACKAGE_THEME)


types = {0: 'Unknown',
         1: 'Extension/Multi-Extension',
         2: 'Full Theme',
         3: 'Dictionary',
         4: 'Language Pack',
         5: 'Search Provider'}

assumed_extensions = {'jar': PACKAGE_THEME,
                      'xml': PACKAGE_SEARCHPROV}


def prepare_package(err, path, expectation=0, for_appversions=None,
                    timeout=-1):
    """Prepares a file-based package for validation.

    timeout is the number of seconds before validation is aborted.
    If timeout is -1 then no timeout checking code will run.
    """

    package = None
    try:
        # Test that the package actually exists. I consider this Tier 0
        # since we may not even be dealing with a real file.
        if not os.path.isfile(path):
            err.error(('main', 'prepare_package', 'not_found'),
                      'The package could not be found')
            return

        # Pop the package extension.
        package_extension = os.path.splitext(path)[1]
        package_extension = package_extension.lower()

        def timeout_handler(signum, frame):
            raise validator.ValidationTimeout(timeout)

        if timeout != -1:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, timeout)

        if package_extension == '.xml':
            test_search(err, path, expectation)
        elif package_extension not in ('.xpi', '.jar'):
            err.error(('main', 'prepare_package', 'unrecognized'),
                      'The package is not of a recognized type.')
        else:
            package = open(path, 'rb')
            test_package(err, package, path, expectation, for_appversions)

        err.metadata['is_extension'] = err.detected_type == PACKAGE_EXTENSION

    except validator.ValidationTimeout:
        err.system_error(
            msg_id='validation_timeout',
            message='Validation has timed out',
            signing_severity='high',
            description=('Validation was unable to complete in the allotted '
                         'time. This is most likely due to the size or '
                         'complexity of your add-on.',
                         'This timeout has been logged, but please consider '
                         'filing an issue report here: '
                         'https://bit.ly/1POrYYU'),
            exc_info=sys.exc_info())

    except Exception:
        err.system_error(exc_info=sys.exc_info())

    finally:
        # Remove timers and signal handlers regardless of whether
        # we've completed successfully or the timer has fired.
        if timeout != -1:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)

        if package:
            package.close()

        decorator.cleanup()


def test_search(err, package, expectation=0):
    'Tests the package to see if it is a search provider.'

    expected_search_provider = expectation in (PACKAGE_ANY,
                                               PACKAGE_SEARCHPROV)

    # If we're not expecting a search provider, warn the user and stop
    # testing it like a search provider.
    if not expected_search_provider:
        return err.warning(('main',
                            'test_search',
                            'extension'),
                           'Unexpected file extension.')

    # Is this a search provider?
    detect_opensearch(err, package, listed=err.get_resource('listed'))

    if expected_search_provider and not err.failed():
        err.detected_type = PACKAGE_SEARCHPROV


def test_package(err, file_, name, expectation=PACKAGE_ANY,
                 for_appversions=None):
    'Begins tests for the package.'

    # Load up a new instance of an XPI.
    try:
        package = XPIManager(file_, mode='r', name=name)

        has_package_json = 'package.json' in package
        has_manifest_json = 'manifest.json' in package
        has_install_rdf = 'install.rdf' in package

        # install.rdf? | package.json? | manifest.json? | error | use-file
        # Yes          | No            | No             | No    | install.rdf
        # Yes          | Yes           | No             | No    | install.rdf
        # Yes          | No            | Yes            | No    | install.rdf
        # No           | No            | Yes            | No    | manifest.json
        # No           | No            | No             | Yes   | install.rdf
        # No           | Yes           | No             | No    | package.json
        # No           | No            | Yes            | Yes   | install.rdf
        if has_package_json:
            _load_package_json(err, package, expectation)
        if has_manifest_json:
            _load_manifest_json(err, package, expectation)
        if has_install_rdf:
            _load_install_rdf(err, package, expectation)
    except IOError:
        # Die on this one because the file won't open.
        err.error(('main', 'test_package', 'unopenable'),
                  'The XPI could not be opened.')
        return
    except (BadZipfile, zlib_error):
        # Die if the zip file is corrupt.
        err.error(('submain', '_load_install_rdf', 'badzipfile'),
                  error='Corrupt ZIP file',
                  description='We were unable to decompress the zip file.')
        return

    if package.extension in assumed_extensions:
        assumed_type = assumed_extensions[package.extension]
        # Is the user expecting a different package type?
        if expectation not in (PACKAGE_ANY, assumed_type):
            err.error(('main', 'test_package', 'unexpected_type'),
                      'Unexpected package type (found theme)')

    test_inner_package(err, package, for_appversions)


def _load_install_rdf(err, package, expectation):
    try:
        install_rdf = RDFParser(err, package.read('install.rdf'))
    except (RDFException, DefusedXmlException) as ex:
        if isinstance(ex, DefusedXmlException):
            url = 'https://pypi.python.org/pypi/defusedxml/0.3#attack-vectors'
            reason = 'Malicious XML was detected, see {0}.'.format(url)
            line = 0
        else:
            reason = ('Try validating your RDF with the W3 validator: '
                      'http://www.w3.org/RDF/Validator/.')
            line = ex.line()
        err.error(
                err_id=('main', 'test_package', 'parse_error'),
                error='Could not parse `install.rdf`.',
                description=('The RDF parser was unable to parse the '
                             'install.rdf file included with this add-on.',
                             reason),
                filename='install.rdf',
                line=line)
        return
    else:
        if install_rdf.rdf is None:
            err.error(
                    err_id=('main', 'test_package', 'cannot_parse_installrdf'),
                    error='Cannot read `install.rdf`',
                    description='The install.rdf file could not be parsed.',
                    filename='install.rdf')
            return
        else:
            err.save_resource('has_install_rdf', True, pushable=True)
            err.save_resource('install_rdf', install_rdf, pushable=True)

    # Load up the results of the type detection
    results = detect_type(err, install_rdf, package)
    if results is None:
        err.error(
                err_id=('main', 'test_package', 'undeterminable_type'),
                error='Unable to determine add-on type',
                description='The type detection algorithm could not determine '
                            'the type of the add-on.')
        return
    else:
        err.detected_type = results

    # Compare the results of the low-level type detection to
    # that of the expectation and the assumption.
    if expectation not in (PACKAGE_ANY, results):
        err.warning(
            err_id=('main', 'test_package', 'extension_type_mismatch'),
            warning='Extension Type Mismatch',
            description=("We detected that the add-on's type does not match "
                         'the expected type.',
                         'Type "%s" expected, found "%s"' %
                         (types[expectation], types[results])))


def _load_package_json(err, package, expectation):
    raw_package_json = package.read('package.json')
    try:
        package_json = json.loads(raw_package_json)
    except ValueError:
        err.error(
            err_id=('main', 'test_package', 'parse_error'),
            error='Could not parse `package.json`.',
            description='The JSON parser was unable to parse the '
                        'package.json file included with this add-on.',
            filename='package.json')
    else:
        err.save_resource('has_package_json', True, pushable=True)
        err.save_resource('package_json', package_json, pushable=True)
        err.detected_type = PACKAGE_EXTENSION


def _load_manifest_json(err, package, expectation):
    raw_manifest_json = package.read('manifest.json')
    try:
        manifest_json = ManifestJsonParser(err, raw_manifest_json)
    except ValueError:
        err.error(
            err_id=('main', 'test_package', 'parse_error'),
            error='Could not parse `manifest.json`.',
            description='The JSON parser was unable to parse the '
                        'manifest.json file included with this add-on.',
            filename='manifest.json')
    else:
        err.save_resource('has_manifest_json', True, pushable=True)
        err.save_resource('manifest_json', manifest_json, pushable=True)
        err.detected_type = PACKAGE_EXTENSION


def populate_chrome_manifest(err, xpi_package):
    "Loads the chrome.manifest if it's present"

    if 'chrome.manifest' in xpi_package:
        chrome_data = xpi_package.read('chrome.manifest')
        chrome = ChromeManifest(chrome_data, 'chrome.manifest')

        chrome_recursion_buster = set()

        # Handle the case of manifests linked from the manifest.
        def get_linked_manifest(path, from_path, from_chrome, from_triple):

            if path in chrome_recursion_buster:
                err.warning(
                    err_id=('submain', 'populate_chrome_manifest',
                            'recursion'),
                    warning='Linked manifest recursion detected.',
                    description='A chrome registration file links back to '
                                'itself. This can cause a multitude of '
                                'issues.',
                    filename=path)
                return

            # Make sure the manifest is properly linked
            if path not in xpi_package:
                err.notice(
                    err_id=('submain', 'populate_chrome_manifest', 'linkerr'),
                    notice='Linked manifest could not be found.',
                    description=('A linked manifest file could not be found '
                                 'in the package.',
                                 'Path: %s' % path),
                    filename=from_path,
                    line=from_triple['line'],
                    context=from_chrome.context)
                return

            chrome_recursion_buster.add(path)

            manifest = ChromeManifest(xpi_package.read(path), path)
            for triple in manifest.triples:
                yield triple

                if triple['subject'] == 'manifest':
                    subpath = triple['predicate']
                    # If the path is relative, make it relative to the current
                    # file.
                    if not subpath.startswith('/'):
                        subpath = '%s/%s' % (
                            '/'.join(path.split('/')[:-1]), subpath)

                    subpath = subpath.lstrip('/')

                    for subtriple in get_linked_manifest(
                            subpath, path, manifest, triple):
                        yield subtriple

            chrome_recursion_buster.discard(path)

        chrome_recursion_buster.add('chrome.manifest')

        # Search for linked manifests in the base manifest.
        for extra_manifest in chrome.get_triples(subject='manifest'):
            # When one is found, add its triples to our own.
            for triple in get_linked_manifest(extra_manifest['predicate'],
                                              'chrome.manifest', chrome,
                                              extra_manifest):
                chrome.triples.append(triple)

        chrome_recursion_buster.discard('chrome.manifest')

        # Create a reference so we can get the chrome manifest later, but make
        # it pushable so we don't run chrome manifests in JAR files.
        err.save_resource('chrome.manifest', chrome, pushable=True)
        # Create a non-pushable reference for tests that need to access the
        # chrome manifest from within JAR files.
        err.save_resource('chrome.manifest_nopush', chrome, pushable=False)


def test_inner_package(err, xpi_package, for_appversions=None):
    "Tests a package's inner content."

    populate_chrome_manifest(err, xpi_package)

    # Iterate through each tier.
    for tier in sorted(decorator.get_tiers()):

        # Let the error bundler know what tier we're on.
        err.set_tier(tier)

        # Iterate through each test of our detected type.
        for test in decorator.get_tests(tier, err.detected_type):
            # Test whether the test is app/version specific.
            if test['versions'] is not None:
                # If the test's version requirements don't apply to the add-on,
                # then skip the test.
                if not err.supports_version(test['versions']):
                    continue

                # If the user's version requirements don't apply to the test or
                # to the add-on, then skip the test.
                if (for_appversions and
                    not (err._compare_version(requirements=for_appversions,
                                              support=test['versions']) and
                         err.supports_version(for_appversions))):
                    continue

            # Save the version requirements to the error bundler.
            err.version_requirements = test['versions']

            test_func = test['test']
            if test['simple']:
                test_func(err)
            else:
                # Pass in:
                # - Error Bundler
                # - A copy of the package itself
                test_func(err, xpi_package)

        # Return any errors at the end of the tier if undetermined.
        if err.failed(fail_on_warnings=False) and not err.determined:
            err.unfinished = True
            err.discard_unused_messages(ending_tier=tier)
            return err

    supports = err.get_resource('supports') or []
    if (err.get_resource('has_install_rdf') and
            not err.get_resource('has_manifest_json') and
            not err.get_resource('is_multiprocess_compatible') and
            err.detected_type in (PACKAGE_EXTENSION, PACKAGE_SUBPACKAGE) and
            'firefox' in supports):
        # If it's an old-style xpi, or a sdk extension, that supports Firefox,
        # but is not a Web Extension, then we raise a warning if multiprocess
        # compatible property was not found in install.rdf.
        format_args = {}
        if err.get_resource('has_package_json'):
            format_args['filename'] = 'package.json'
            format_args['field'] = 'multiprocess'
            format_args['link'] = (
                MDN_DOC %
                'Mozilla/Add-ons/SDK/Guides/Multiprocess_Firefox_and_the_SDK')
        else:
            format_args['filename'] = 'install.rdf'
            format_args['field'] = '<em:multiprocessCompatible>'
            format_args['link'] = (
                MDN_DOC % 'Mozilla/Add-ons/Working_with_multiprocess_Firefox')
        err.warning(
            ('submain', 'test_inner_package', 'not_multiprocess_compatible'),
            'Extension is not marked as compatible with Multi Process',
            "Your extension is not marked as compatible with "
            "Multi-Process Firefox and may not work in future versions "
            "of Firefox. Please review it, make changes if needed and "
            "set {field} to true in {filename} if it's compatible. "
            "See {link} for more information.".format(**format_args))

    # Return the results.
    return err
