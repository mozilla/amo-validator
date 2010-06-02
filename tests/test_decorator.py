import decorator

@decorator.register_test(tier=1)
def arbitrary_test():
    return
    
@decorator.register_test(tier=2, expected_type=5)
def arbitrary_test_two():
    return
    
@decorator.register_test(tier=2)
def arbitrary_test_three():
    return
    
@decorator.register_test(tier=2, simple=True)
def arbitrary_test_four():
    return
    

def test_tiers():
    """Tests to make sure that the decorator module is properly
    registering test functions."""
    
    tiers = decorator.get_tiers()
    assert len(tiers) == 2
    
def test_specifictype():
    """Tests to make sure that the decorator module can return test of
    a specific type."""
    
    tests = list(decorator.get_tests(2, 1))
    assert len(tests) == 2
    
def test_assumedtype():
    """Tests to see if the decorator module can find tests for generic
    as well as specific types"""
    
    tests = list(decorator.get_tests(2, 5))
    assert len(tests) == 3
    