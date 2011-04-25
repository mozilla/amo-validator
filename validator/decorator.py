
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
