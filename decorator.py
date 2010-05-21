
# This module is FABULOUS!


test_tiers = {}

def register_test(tier, test, expected_type=None):
    "Registers a test to be run during validation."
    global test_tiers
    
    # If the test tier doesn't exist, then add it in.
    if not tier in test_tiers:
        test_tiers[tier] = []
    
    test_tiers[tier].append({"test": test,
                             "type": expected_type})
    
def get_tiers():
    "Returns a list of tier values."
    global test_tiers
    return test_tiers.keys()
    
def run_tests(tier, type_=None):
    "Returns a generator of test functions."
    
    # List comprehension to sort and filter and the like.
    tests = [test["test"] for test in test_tiers[tier] if \
             test["type"] in (None, 0, type_)]
    
    # Iterate and yield
    for test in tests:
        yield test