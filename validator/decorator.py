import logging

import validator.constants
from validator.constants import APPLICATIONS


log = logging.getLogger('amo.validator')


TEST_TIERS = {}
CLEANUP_FUNCTIONS = []


def register_test(tier=1, expected_type=None, simple=False, versions=None):
    'Registers tests for the validation flow.'

    def wrap(function):
        'Wrapper function to decorate registered tests.'

        # Make sure the tier exists before we add to it
        if tier not in TEST_TIERS:
            TEST_TIERS[tier] = []

        # Add a test object to the test's tier
        TEST_TIERS[tier].append({'test': function,
                                 'type': expected_type,
                                 'simple': simple,
                                 'versions': versions})

        # Return the function to be run
        return function

    # Return the wrapping function (for use as a decorator)
    return wrap


def register_cleanup(cleanup):
    """Register a cleanup function to be called at the end of every validation
    task. Takes either a callable (including a class with a __call_ method),
    or a class with a `cleanup` class method."""

    if not callable(cleanup):
        # Allow decorating a class with a `cleanup` classm ethod.
        cleanup = cleanup.cleanup

    CLEANUP_FUNCTIONS.append(cleanup.cleanup)
    return cleanup


def cleanup():
    """Call every cleanup function which has been registered via
    @register_cleanup."""

    for fn in CLEANUP_FUNCTIONS:
        try:
            fn()
        except Exception, e:
            log.exception('Error during cleanup: %s' % e)


def get_tiers():
    'Returns a list of tier values.'
    return TEST_TIERS.keys()


def get_tests(tier, type_=None):
    'Returns a generator of test functions.'

    # List of acceptable types
    types = (None, 0, type_)

    # Current Tier
    ctier = TEST_TIERS[tier]

    # List comprehension to sort and filter and the like.
    return (test for test in ctier if test['type'] in types)


def version_range(guid, version, before=None, app_versions=None):
    """Returns all values after (and including) `version` for the app `guid`"""

    if app_versions is None:
        app_versions = validator.constants.APPROVED_APPLICATIONS
    app_key = None

    # Support for shorthand instead of full GUIDs.
    for app_guid, app_name in APPLICATIONS.items():
        if app_name == guid:
            guid = app_guid
            break

    for key in app_versions.keys():
        if app_versions[key]['guid'] == guid:
            app_key = key
            break

    if not app_key or version not in app_versions[app_key]['versions']:
        raise Exception('Bad GUID or version provided for version range: %s'
                        % version)

    all_versions = app_versions[app_key]['versions']
    version_pos = all_versions.index(version)
    before_pos = None
    if before is not None and before in all_versions:
        before_pos = all_versions.index(before)
    return all_versions[version_pos:before_pos]
