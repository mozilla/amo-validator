import decorator

def test_tiers():
    """Tests to make sure that the decorator module is properly
    registering test functions."""
    
    decorator.TEST_TIERS = {}
    
    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)
    
    tiers = decorator.get_tiers()
    print tiers
    assert len(tiers) == 2
    
def test_specifictype():
    """Tests to make sure that the decorator module can return a test
    of a specific type."""
    
    decorator.TEST_TIERS = {}
    
    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)
    
    tests = list(decorator.get_tests(2, 1))
    assert len(tests) == 2
    
def test_assumedtype():
    """Tests to see if the decorator module can find tests for generic
    as well as specific types"""
    
    decorator.TEST_TIERS = {}
    
    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)
    
    tests = list(decorator.get_tests(2, 5))
    assert len(tests) == 3
    