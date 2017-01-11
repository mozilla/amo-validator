from validator import decorator
from validator.constants import PACKAGE_THEME
from validator import metadata_helpers


OPTIONS_TYPE_VALUES = ('1', '2', '3')


@decorator.register_test(tier=1)
def test_install_rdf_params(err, xpi_package=None):
    """Tests to make sure that some of the values in install.rdf
    are not gummed up."""

    if not err.get_resource('has_install_rdf'):
        return

    install = err.get_resource('install_rdf')

    # This returns for testing reasons
    return _test_rdf(err, install)


def _test_rdf(err, install):
    """Wrapper for install.rdf testing to make unit testing so much
    easier."""

    is_compat = err.get_resource('is_compat_test')

    shouldnt_exist = {'hidden'}
    if err.get_resource('listed'):
        shouldnt_exist |= {'updateURL', 'updateKey'}
    obsolete = {'file', 'skin', 'requires'}
    must_exist_once = {'id',
                       'version',
                       'name',
                       'targetApplication'}

    may_exist_once = {'about',  # For <Description> element
                      'bootstrap',
                      'optionsURL',
                      'aboutURL',
                      'iconURL',
                      'icon64URL',
                      'homepageURL',
                      'creator',
                      'multiprocessCompatible',
                      'hasEmbeddedWebExtension',
                      'optionsType',
                      'type',
                      'updateKey',
                      'updateURL',
                      'skinnable',
                      'strictCompatibility',
                      'unpack'}  # This has other rules; CAUTION!

    # Support a name requirement override.
    if err.overrides and err.overrides.get('ignore_empty_name'):
        must_exist_once.remove('name')
        may_exist_once.add('name')

    may_exist = {'targetApplication',
                 'localized',
                 'description',
                 'creator',
                 'translator',
                 'contributor',
                 'targetPlatform',
                 'requires',
                 'developer'}

    if (err.detected_type == PACKAGE_THEME or
        (err.subpackages and
         err.subpackages[0]['detected_type'] == PACKAGE_THEME)):
        must_exist_once.add('internalName')

    top_id = install.get_root_subject()

    predicates = {}

    for pred_raw in install.rdf.predicates(top_id, None):
        predicate = pred_raw.split('#')[-1]

        value = install.get_object(top_id, pred_raw)
        predicates[predicate] = value

        # Mark that the unpack element has been supplied
        if predicate == 'unpack':
            err.save_resource('em:unpack', value, pushable=True)

        elif predicate == 'bootstrap':
            err.save_resource('em:bootstrap', value)
            err.metadata['bootstrapped'] = value == 'true'

        elif predicate == 'multiprocessCompatible':
            err.save_resource('is_multiprocess_compatible', value == 'true')

        elif predicate == 'strictCompatibility':
            err.metadata['strict_compatibility'] = value == 'true'

        elif predicate == 'hasEmbeddedWebExtension':
            err.notice(('testcases_installrdf',
                        '_test_rdf',
                        'hasEmbeddedWebExtension'),
                       'This add-on contains an embedded webextension',
                       'The embedded webextension is in the folder "webextension". '
                       'Handle validation messages with care. For more information, refer to '
                       'https://developer.mozilla.org/en-US/Add-ons/WebExtensions/Embedded_WebExtensions',
                       'install.rdf')
            err.save_resource('has_embedded_webextension', value == 'true')

        # We skip over install.rdf tests during bulk validation. See bug 735841
        elif predicate in shouldnt_exist and not is_compat:
            err.error(('testcases_installrdf',
                       '_test_rdf',
                       'shouldnt_exist'),
                      'Banned element in install.rdf',
                      """The element "%s" was found in the add-on's
                      install.rdf file. It is not allowed in add-ons under
                      the current configuration.""" % predicate,
                      'install.rdf')
            continue

        # Test if the predicate is obsolete
        elif predicate in obsolete and not is_compat:
            err.notice(('testcases_installrdf',
                        '_test_rdf',
                        'obsolete'),
                       'Obsolete element in install.rdf',
                       "The element \"%s\" was found in the add-on's "
                       'install.rdf file. It has not been banned, but it is '
                       'no longer supported by any modern Mozilla product. '
                       'Removing the element is recommended and will not '
                       'break support.' % predicate,
                       'install.rdf')
            continue

        # Remove the predicate from must_exist_once if it's there.
        if predicate in must_exist_once:
            # Test the predicate for specific values.
            if predicate in PREDICATE_TESTS:
                PREDICATE_TESTS[predicate](err, value, source='install.rdf')

            must_exist_once.remove(predicate)
            continue

        # Do the same for may_exist_once.
        elif predicate in may_exist_once:
            if (predicate == 'optionsType' and
                    str(value) not in OPTIONS_TYPE_VALUES) and not is_compat:
                err.warning(
                    err_id=('testcases_installrdf', '_test_rdf',
                            'optionsType'),
                    warning='<em:optionsType> has bad value.',
                    description=('The value of <em:optionsType> must be one '
                                 'of: %s.' % ', '.join(OPTIONS_TYPE_VALUES),
                                 'Value found: %s' % value),
                    filename='install.rdf')

            may_exist_once.remove(predicate)
            continue

        # If the element is safe for repetition, continue
        elif predicate in may_exist:
            continue

        # If the predicate isn't in any of the above lists, it is
        # invalid and needs to go.
        if not is_compat:
            err.notice(('testcases_installrdf',
                        '_test_rdf',
                        'unrecognized'),
                       'Unrecognized element in install.rdf',
                       ['An element was found in the install manifest, however it '
                        'does not appear to be a part of the specification, it '
                        'has been used too many times, or is not applicable to '
                        'the current configuration.',
                        'Detected element: <em:%s>' % predicate],
                       'install.rdf')

    # We skip over install.rdf tests during bulk validation. See bug 735841
    if not is_compat:
        if not err.get_resource('listed'):
            if 'updateURL' in predicates:
                if not (str(predicates['updateURL']).lower().startswith('https:')
                        or 'updateKey' in predicates):
                    # TODO: Validate updateKey value
                    err.notice(('testcases_installrdf',
                                '_test_rdf',
                                'missing_updateKey'),
                               'Missing updateKey element',
                               'Your updateURL is not served over a secure '
                               'connection, and your install.rdf does not '
                               'specify an update key. This means that serving '
                               'updates for this version will not be possible.',
                               'install.rdf',
                               signing_severity='trivial')
            else:
                err.notice(('testcases_installrdf',
                            '_test_rdf',
                            'missing_updateURL'),
                           'Missing updateURL element',
                           'Your add-on does not specify an update URL. This '
                           'means that it will be impossible for you to serve '
                           'updates to this add-on which are not listed publicly '
                           'on addons.mozilla.org.',
                           'install.rdf',
                           signing_severity='trivial')

        # Once all of the predicates have been tested, make sure there are
        # no mandatory elements that haven't been found.
        if must_exist_once:
            err.error(('testcases_installrdf',
                       '_test_rdf',
                       'missing_addon'),
                      'install.rdf missing element(s).',
                      ['The element listed is a required element in the install '
                       'manifest specification. It must be added to your addon.',
                       'Missing elements: %s' % ', '.join(must_exist_once)],
                      'install.rdf')


PREDICATE_TESTS = {
    'id': metadata_helpers.validate_id,
    'version': metadata_helpers.validate_version,
    'name': metadata_helpers.validate_name,
}
