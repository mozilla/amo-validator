import os
from StringIO import StringIO

import fastchardet
import fnmatch

from validator import decorator
from validator.chromemanifest import ChromeManifest
from validator.constants import PACKAGE_EXTENSION, PACKAGE_LANGPACK
from validator.xpi import XPIManager

from .l10n import dtd, properties


# The threshold that determines the number of entities that must not be
# missing from the package.
L10N_THRESHOLD = 0.35
L10N_SIMILAR_THRESHOLD = 0.9  # For en_US/en_GB kind of stuff

# Only warn about unchanged entities longer than this number of characters.
L10N_LENGTH_THRESHOLD = 3

# To avoid noise, this value ensures that the percent of unchanged entities
# is not inflated due to small numbers of entities.
L10N_MIN_ENTITIES = 18

LOCALE_CACHE = {}


def _list_locales(err, xpi_package=None):
    'Returns a raw list of locales from chrome.manifest'

    chrome = None
    if xpi_package is not None:
        # Handle a reference XPI
        chrome = ChromeManifest(xpi_package.read('chrome.manifest'),
                                'chrome.manifest')
    else:
        # Handle the current XPI
        chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return None

    pack_locales = chrome.get_triples('locale')
    return list(pack_locales)

def _get_locales(err, xpi_package=None, locales=None):
    'Returns a list of locales from the chrome.manifest file.'

    if locales is None:
        locales = _list_locales(err, xpi_package)
    if not locales:
        return None

    processed_locales = {}
    for locale in locales:
        locale_jar = locale['object'].split()

        location = locale_jar[-1]

        # Locales can be bundled in JARs
        jarred = location.startswith('jar:')
        if jarred:
            # We just care about the JAR path
            location = location[4:]
            split_location = location.split('!', 2)
            # Ignore malformed JAR URIs.
            if len(split_location) < 2:
                continue

            path, location = split_location

        locale_desc = {'predicate': locale['predicate'],
                       'target': location,
                       'name': locale_jar[0],
                       'jarred': jarred}
        if jarred:
            locale_desc['path'] = path

        locale_name = '%s:%s' % (locale['predicate'], locale_jar[0])
        if locale_name not in processed_locales:
            processed_locales[locale_name] = locale_desc

    return processed_locales


def _get_locale_manager(err, xpi_package, description,
                        no_cache=False):
    'Returns the XPIManager object for a locale'

    if not description['jarred']:
        return xpi_package

    path = description['path']

    if path in LOCALE_CACHE and not no_cache:
        return LOCALE_CACHE[path]

    if path not in xpi_package:
        # TODO: Pass the filename of the triple's manifest.
        err.warning(('testcases_l10ncompleteness',
                     '_get_locale_manager',
                     'manager_absent'),
                    'Listed locale does not exist',
                    ['A locale JAR is listed in chrome.manifest, but it could '
                     'not be located. Check the spelling and capitalization '
                     'of the path.',
                     'Missing JAR: %s' % path],
                    filename='chrome.manifest')
        return None
    jar = StringIO(xpi_package.read(path))
    locale = XPIManager(jar, mode='r', name=path)

    if not no_cache:
        LOCALE_CACHE[path] = locale
    return locale


@decorator.register_test(tier=4)
def test_xpi(err, xpi_package):
    """Tests an XPI (or JAR, really) for L10n completeness"""

    # Skip over incompatible (or unnecessary) package types.
    if (err.detected_type != PACKAGE_EXTENSION or
        err.is_nested_package):
        return None

    # Don't even both with the test(s) if there's no chrome.manifest.
    if 'chrome.manifest' not in xpi_package:
        return None

    raw_locales = _list_locales(err)

    # We need at least a reference and a target.
    num_locales = len(raw_locales)
    if num_locales < 2:
        if num_locales == 0:
            # TODO: Pass the filename of the triple's manifest.
            err.notice(('testcases_l10ncompleteness',
                        'test_xpi',
                        'no_locales'),
                       'Add-on appears not to be localized',
                       "The add-on doesn't have any locale entries in its "
                       'chrome.manifest file, which suggests that it may '
                       'not be localized.',
                       filename='chrome.manifest')
        return

    locales = _get_locales(err, None, raw_locales)

    # Use the first locale by default
    ref_lang = locales.values()[0]['name']
    # Try to find en-US, as this is where the majority of users is.
    if ref_lang != 'en-US':
        for name, locale in locales.items():
            if locale['name'] == 'en-US':
                ref_lang = 'en-US'
                break

    references = {}
    for locale_name, locale in locales.items():
        if locale['name'] == ref_lang:
            references[locale_name] = locale

    references_locales = {}
    for ref_name, reference in references.items():
        references_locales[ref_name] = \
                _get_locale_manager(err, xpi_package, reference)

    def get_reference(locale):
        for r_name, r in references.items():
            if r['predicate'] == locale['predicate']:
                return r_name, r
        return None, None

    # Loop through the locales and test the valid ones.
    for name, locale in locales.items():
        # Ignore the reference locale
        if name in references:
            continue

        ref_name, reference = get_reference(locale)

        # If we can't find a reference for the current namespace, bail.
        if reference is None or ref_name is None:
            continue

        target_locale = _get_locale_manager(err,
                                            xpi_package,
                                            locale)
        # If we can't find the target locale, just bail.
        if target_locale is None:
            continue

        # Isolate each of the target locales' results.
        results = _compare_packages(references_locales[ref_name],
                                    target_locale,
                                    reference['target'],
                                    locale['target'])
        similar = reference['name'].startswith(locale['name'].split('-')[0])
        _aggregate_results(err, results, locale, similar)


@decorator.register_test(tier=4, expected_type=PACKAGE_LANGPACK)
def test_lp_xpi(err, xpi_package):
    'Tests a language pack for L10n completeness'

    # Don't even both with the test(s) if there's no chrome.manifest.
    if 'chrome.manifest' not in xpi_package:
        return None

    locales = _get_locales(err)

    # Get the reference packages.
    references = []
    support_references = err.get_resource('supports')
    if not support_references:
        references.append('firefox')
        err.info(('testcases_l10ncompleteness',
                  'test_lp_xpi',
                  'missing_app_support'),
                 'Supported app missing in localization completeness.',
                 'While testing in localization comleteness, a list of '
                 'supported applications for the language pack was not found. '
                 'This is likely because there are no listed '
                 '<em:targetApplication> elements in the install.rdf file.')
    else:
        for support in support_references:
            ref_xpi = XPIManager(os.path.join(os.path.dirname(__file__),
                                              'langpacks/%s.xpi' % support))
            ref_xpi.app_name = support
            reference_locales = _get_locales(None, ref_xpi)

            references.append((ref_xpi, reference_locales))

    # Iterate each supported reference package
    for (ref_xpi, ref_locales) in references:
        # Iterate each locale in each supported reference package
        ref_pack = _get_locale_manager(err,
                                       ref_xpi,
                                       {'path': 'en-US.jar',
                                        'jarred': True},
                                       no_cache=True)
        for ref_locale_name in ref_locales:
            ref_locale = ref_locales[ref_locale_name]
            ref_predicate = ref_locale['predicate']
            corresp_locales = [locales[name] for name
                               in locales
                               if locales[name]['predicate'] == ref_predicate]
            # If we found no matching locale, then it's missing from the pack
            if not corresp_locales:
                err.warning(('testcases_l10ncompleteness',
                             'test_lp_xpi',
                             'find_corresponding_locale'),
                            'Could not find corresponding locale',
                            ['A locale was found in the reference package, '
                             'however it was not found in the target package.',
                             'Missing locale: %s' % ref_predicate],
                            filename='chrome.manifest')
                continue

            target_locale = corresp_locales[0]
            target_pack = _get_locale_manager(err,
                                              xpi_package,
                                              target_locale)
            if target_pack is None:
                continue

            results = _compare_packages(reference=ref_pack,
                                        target=target_pack,
                                        ref_base=ref_locale['target'],
                                        locale_base=target_locale['target'])

            # Report the findings after each supported app's locale
            _aggregate_results(err, results, target_locale)

    # Clear the cache at the end of the test
    LOCALE_CACHE.clear()


def _compare_packages(reference, target, ref_base='', locale_base=''):
    'Compares two L10n-compatible packages to one another.'

    tar_files = target.package_contents()

    results = []
    total_entities = 0

    ref_base = ref_base.lstrip('/')
    locale_base = locale_base.lstrip('/')

    l10n_docs = ('dtd', 'properties', 'xhtml', 'ini', 'inc')
    parsable_docs = ('dtd', 'properties')

    for name in reference:

        entity_count = 0

        # Skip directory entries.
        if name.endswith('/'):  # pragma: no cover
            continue

        # Ignore files not considered reference files.
        if ref_base and not name.startswith(ref_base):
            continue

        extension = name.split('.')[-1]
        if extension not in l10n_docs:
            continue
        parsable = extension in parsable_docs

        if parsable:
            ref_doc = _parse_l10n_doc(name,
                                      reference.read(name),
                                      no_encoding=True)
        else:
            ref_doc = ()

        tar_name = locale_base + name[len(ref_base):]
        if tar_name not in tar_files:
            results.append({'type': 'missing_files',
                            'entities': len(ref_doc),
                            'filename': tar_name})
            continue

        if not parsable:
            continue

        tar_doc = _parse_l10n_doc(tar_name, target.read(tar_name))

        if not tar_doc.expected_encoding:
            results.append({'type': 'unexpected_encoding',
                            'filename': tar_name,
                            'expected_encoding': tar_doc.suitable_encoding})

        missing_entities = []
        unchanged_entities = []

        for rname, rvalue, rline in ref_doc.items:
            entity_count += 1

            if rname not in tar_doc.entities:
                missing_entities.append(rname)
                continue

            if (not rname.startswith('pref.timezone.') and
                rvalue == tar_doc.entities[rname] and
                len(rvalue) > L10N_LENGTH_THRESHOLD and
                not fnmatch.fnmatch(rvalue, 'http*://*')):

                unchanged_entities.append((rname, rline))
                continue

        if missing_entities:
            results.append({'type': 'missing_entities',
                            'entities': len(missing_entities),
                            'filename': tar_name,
                            'missing_entities': missing_entities})
        if unchanged_entities:
            results.append({'type': 'unchanged_entity',
                            'entities': len(unchanged_entities),
                            'filename': tar_name,
                            'unchanged_entities': unchanged_entities})

        results.append({'type': 'file_entity_count',
                        'filename': tar_name,
                        'entities': entity_count})

        total_entities += entity_count

    results.append({'type': 'total_entities',
                    'entities': total_entities})
    return results


def _parse_l10n_doc(name, doc, no_encoding=False):
    'Parses an L10n document.'

    extension = name.split('.')[-1].lower()

    handlers = {'dtd': dtd.DTDParser,
                'properties': properties.PropertiesParser}
    # These are expected encodings for the various files.
    handler_formats = ('ASCII', 'UTF_8')
    if extension not in handlers:
        return None

    wrapper = StringIO(doc)
    loc_doc = handlers[extension](wrapper)

    # Allow the parse to specify files to skip for encoding checks
    if not no_encoding:
        try:
            # This is much faster than fastchardet, and succeeds more often
            # than fails.
            doc.decode('utf-8')
            encoding = 'UTF_8'
        except UnicodeDecodeError:
            encoding = fastchardet.detect(doc)['encoding'].upper()
        loc_doc.expected_encoding = encoding in handler_formats
        loc_doc.suitable_encoding = handler_formats

    return loc_doc


def _aggregate_results(err, results, locale, similar=False, base='en-US'):
    """Compiles the errors and warnings in the L10n results list into
    error bundler errors and warnings."""

    total_entities = 0
    unchanged_entity_list = {}
    entity_count = {}
    unexpected_encodings = []

    for ritem in results:
        if 'filename' in ritem:
            rfilename = ritem['filename']

        rtype = ritem['type']
        if rtype == 'missing_files':
            err.warning(('testcases_l10ncompleteness',
                        '_aggregate_results',
                        'missing_file'),
                       'Missing translation file',
                       ['Localizations must include a translated copy of each '
                        'file in the reference locale. The required files may '
                        'vary from target application to target application.',
                        'Missing translation file: %s' % rfilename],
                      locale['target'])
        elif rtype == 'missing_entities':
            err.warning(('testcases_l10ncompleteness',
                         '_aggregate_results',
                         'missing_translation_entity'),
                        'Missing translation entity',
                        ['Localizations must include a translated copy of each '
                         'entity from each file in the reference locale. The '
                         'required files may vary from target application to '
                         'target application.',
                         'Missing Entities: %s' %
                             ', '.join(ritem['missing_entities'])],
                        [locale['target'], rfilename])
        elif rtype == 'unchanged_entity':
            filename = ritem['filename']
            if filename not in unchanged_entity_list:
                unchanged_entity_list[filename] = {'count': 0,
                                                   'entities': []}
            unchanged = unchanged_entity_list[filename]
            unchanged['count'] += ritem['entities']
            unchanged['entities'].extend(ritem['unchanged_entities'])
        elif rtype == 'total_entities':
            total_entities += ritem['entities']
        elif rtype == 'file_entity_count':
            entity_count[ritem['filename']] = ritem['entities']
        elif rtype == 'unexpected_encoding':
            unexpected_encodings.append(
                    (ritem['filename'],
                     ', '.join(ritem['expected_encoding'])))

    # Determine the locale's filename argument in advance since we'll use it
    # for every message
    locale_filename = [locale['target']]
    if locale['jarred']:
        locale_filename.append(locale['path'].lstrip('/'))

    agg_unchanged = []
    if not similar:
        unchanged_percentage = L10N_THRESHOLD
    else:
        unchanged_percentage = L10N_SIMILAR_THRESHOLD
    for name, count in entity_count.items():
        if name not in unchanged_entity_list or \
           count == 0:
            continue

        unchanged = unchanged_entity_list[name]
        total_adjusted = max(count, L10N_MIN_ENTITIES)
        percentage = float(unchanged['count']) / float(total_adjusted)
        if percentage >= unchanged_percentage:
            agg_unchanged.append(
                    '%s: %d/%d entities unchanged (%s) at %d percent' %
                    (name,
                     unchanged['count'],
                     count,
                     ', '.join(['%s (%d)' % (e, line)
                                for e, line
                                in unchanged['entities']]),
                     percentage * 100))

    if agg_unchanged:
        err.notice(('testcases_l10ncompleteness',
                    '_aggregate_results',
                    'unchanged_entities'),
                   'Unchanged translation entities',
                   ['Localizations must include a translated copy of each '
                    'entity from each file in the reference locale. These '
                    'translations SHOULD differ from the localized text in '
                    'the reference package.',
                    agg_unchanged],
                   locale_filename)

    if unexpected_encodings:
        # Compile all of the encoding errors into one nice warning.
        compilation = ['Detected files:']
        for target in unexpected_encodings:
            compilation.append('%s\n (expected: %s)' % target)

        err.warning(('testcases_l10ncompleteness',
                     '_aggregate_results',
                     'unexpected_encodings'),
                    'Unexpected encodings in locale files',
                    ['Localization files were encountered that used encodings '
                     'that are not characteristic of those types of files.',
                     '\n'.join(compilation),
                     'Localization files with the wrong encoding can cause '
                     'issues with locales that include non-ASCII characters.'],
                    locale_filename)

