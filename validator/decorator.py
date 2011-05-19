import validator.constants
from validator.constants import *


TEST_TIERS = {}


def register_test(tier=1, expected_type=None, simple=False, versions=None):
    "Registers tests for the validation flow."

    def wrap(function):
        "Wrapper function to decorate registered tests."

        # Make sure the tier exists before we add to it
        if tier not in TEST_TIERS:
            TEST_TIERS[tier] = []

        # Add a test object to the test's tier
        TEST_TIERS[tier].append({"test": function,
                                 "type": expected_type,
                                 "simple": simple,
                                 "versions": versions})

        # Return the function to be run
        return function

    # Return the wrapping function (for use as a decorator)
    return wrap


def get_tiers():
    "Returns a list of tier values."
    return TEST_TIERS.keys()


def get_tests(tier, type_=None):
    "Returns a generator of test functions."

    # List of acceptable types
    types = (None, 0, type_)

    # Current Tier
    ctier = TEST_TIERS[tier]

    # List comprehension to sort and filter and the like.
    return (test for test in ctier if test["type"] in types)


def versions_after(guid, version):
    """Returns all values after (and including) `version` for the app `guid`"""

    app_versions = validator.constants.APPROVED_APPLICATIONS
    app_key = None

    # Support for shorthand instead of full GUIDs.
    for app_guid, app_name in APPLICATIONS.items():
        if app_name == guid:
            guid = app_guid
            break

    for key in app_versions.keys():
        if app_versions[key]["guid"] == guid:
            app_key = key
            break

    if not app_key or version not in app_versions[app_key]["versions"]:
        raise Exception("Bad GUID or version provided for version range")

    version_pos = app_versions[app_key]["versions"].index(version)
    return app_versions[app_key]["versions"][version_pos:]

