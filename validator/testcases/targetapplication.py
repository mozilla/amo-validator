import validator.constants
from validator import decorator
from validator.constants import FF4_MIN, APPLICATIONS

APP_VERSIONS_URL = 'Please check the list of valid versions at: '\
        'https://addons.mozilla.org/en-US/firefox/pages/appversions/'


@decorator.register_test(tier=1)
def test_targetedapplications(err, xpi_package=None):
    """Tests to make sure that the targeted applications in the
    manifest file are legit and that any associated files (I'm
    looking at you, SeaMonkey) are where they need to be."""

    manifest_json = err.get_resource('manifest_json')
    install_rdf = err.get_resource('install_rdf')

    if install_rdf:
        applications = install_rdf.get_applications()
        manifest_file = 'install.rdf'
    elif manifest_json:
        applications = manifest_json.get_applications()
        manifest_file = 'manifest.json'
    else:  # No manifest.json, no install.rdf file.
        if err.supported_versions is None:
            err.supported_versions = {}
        return

    APPROVED_APPLICATIONS = validator.constants.APPROVED_APPLICATIONS
    # Compute APPROVED_IDS dynamically here because APPROVED_APPLICATIONS
    # is a changing constant (updated on the fly on validate.validate).
    APPROVED_IDS = dict((x['guid'], y) for (y, x)
                        in APPROVED_APPLICATIONS.items()
                        if x['guid'] in APPLICATIONS)

    used_targets = []
    all_supported_versions = {}

    err.metadata['applications'] = {}

    # Isolate all of the bnodes referring to target applications
    for target_app in applications:
        guid = target_app['guid']

        used_targets.append(guid)

        found_id = APPROVED_IDS.get(guid)

        if found_id:
            # Remember if the addon supports Firefox.
            is_firefox = APPLICATIONS[guid] == 'firefox'

            # Grab the minimum and maximum version numbers.
            if (err.overrides and
                    'targetapp_minVersion' in err.overrides and
                    guid in err.overrides['targetapp_minVersion']):
                min_version = err.overrides['targetapp_minVersion'][guid]
            else:
                min_version = target_app.get('min_version')

            if (err.overrides and
                    'targetapp_maxVersion' in err.overrides and
                    guid in err.overrides['targetapp_maxVersion']):
                max_version = err.overrides['targetapp_maxVersion'][guid]
            else:
                max_version = target_app.get('max_version')

            # Get the approved app versions for this application.
            app_versions = APPROVED_APPLICATIONS[found_id]['versions']

            # Ensure that the version numbers are in the app's
            # list of acceptable version numbers.

            app_name = APPLICATIONS[guid] if guid in APPLICATIONS else guid

            if min_version is None:
                err.error(('testcases_targetapplication',
                           'test_targetedapplications',
                           'missing_minversion'),
                          'Missing minVersion property',
                          'A target application element is missing its '
                          'min version property.',
                          filename=manifest_file)
                continue
            elif max_version is None:
                err.error(('testcases_targetapplication',
                           'test_targetedapplications',
                           'missing_maxversion'),
                          'Missing maxVersion property',
                          'A target application element is missing its '
                          'max version property.',
                          filename=manifest_file)
                continue

            try:
                min_ver_pos = app_versions.index(min_version)
            except ValueError:
                err.error(('testcases_targetapplication',
                           'test_targetedapplications',
                           'invalid_min_version'),
                          'Invalid minimum version number',
                          ['The minimum version that was specified is not '
                           'an acceptable version number for the Mozilla '
                           'product that it corresponds with.',
                           'Version "%s" isn\'t compatible with "%s".' %
                              (min_version, app_name),
                           APP_VERSIONS_URL],
                          manifest_file)
                continue

            try:
                max_ver_pos = app_versions.index(max_version)
            except ValueError:
                err.error(('testcases_targetapplication',
                           'test_targetedapplications',
                           'invalid_max_version'),
                          'Invalid maximum version number',
                          ['The maximum version that was specified is not '
                           'an acceptable version number for the Mozilla '
                           'product that it corresponds with.',
                           'Version "%s" isn\'t compatible with "%s".' %
                              (max_version, app_name),
                           APP_VERSIONS_URL],
                          manifest_file)
                continue

            # Now we need to check to see if the version numbers
            # are in the right order.
            if min_ver_pos > max_ver_pos:
                err.error(('testcases_targetapplication',
                           'test_targetedapplications',
                           'invalid_version_order'),
                          'Invalid min/max versions',
                          ['The version numbers provided for the '
                           'application in question are not in the '
                           'correct order. The maximum version must be '
                           'greater than the minimum version.',
                           '"%s" is not less than "%s".' % (min_version,
                                                            max_version)],
                          manifest_file)
                continue

            all_supported_versions[guid] = (
                app_versions[min_ver_pos:max_ver_pos + 1])

            err.metadata['applications'][APPLICATIONS[guid]] = {
                'min': min_version,
                'max': max_version,
            }

            # Test whether it's a FF4 addon

            # NOTE: This should probably also be extrapolated for
            # Thunderbird and the like when they get up to speed. The tests
            # will likely be the same down the line, so we can keep the
            # "ff4" resource as a legacy thing and worry about it later.
            if is_firefox:
                ff4_pos = app_versions.index(FF4_MIN)
                if max_ver_pos >= ff4_pos:
                    err.save_resource('ff4', True)

    no_duplicate_targets = set(used_targets)

    if len(used_targets) != len(no_duplicate_targets):
        err.error(('testcases_targetapplication',
                   'test_targetedapplications',
                   'duplicate_targetapps'),
                  'Found duplicate target application elements.',
                  'Multiple target application elements were found in the '
                  'manifest file that refer to the same application GUID. '
                  'There should not be duplicate target applications '
                  'entries.',
                  'install.rdf')

    # This finds the UUID of the supported applications and puts it in
    # a fun and easy-to-use format for use in other tests.
    final_guids = map(str, no_duplicate_targets)
    approved_guids = list(set(final_guids).intersection(APPROVED_IDS.keys()))
    supports = [APPLICATIONS[k] for k in approved_guids]
    err.save_resource('supports', supports)

    if not err.supported_versions:  # if not set for compatibility
        err.supported_versions = all_supported_versions

    if not supports and err.get_resource('listed'):
        err.error(
            err_id=('testcases_targetapplication',
                    'test_targetedapplications',
                    'no_mozilla_support'),
            error='No Mozilla products listed as target applications',
            description=(
                'None of the target applications listed in the manifest are '
                'supported Mozilla products. At least one official Mozilla '
                'product must be supported for inclusion on '
                'addons.mozilla.org.',
                'See https://addons.mozilla.org/firefox/pages/appversions/'
                ' for more information on supported target applications on '
                'AMO.'),
            filename=manifest_file)
