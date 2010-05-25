
# This module is FABULOUS!

test_tiers = {}

def register_test(tier=1, expected_type=None):
    "Registers tests for the validation flow."
    
    def wrap(f):
        
        global test_tiers
        
        if not tier in test_tiers:
            test_tiers[tier] = []
        
        test_tiers[tier].append({"test": f,
                                 "type": expected_type})
        
        def wrapped_f(*args):
            f(*args)
        return wrapped_f
        
    return wrap
    
    
def get_tiers():
    "Returns a list of tier values."
    return test_tiers.keys()

def run_tests(tier, type_=None):
    "Returns a generator of test functions."

    # List comprehension to sort and filter and the like.
    return (test["test"] for test in test_tiers[tier] if
            test["type"] in (None, 0, type_))
