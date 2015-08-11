from nose.tools import eq_

import validator.decorator as decorator


def test_tiers():
    """
    Tests to make sure that the decorator module is properly registering test
    functions.
    """

    dtt = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)

    tiers = decorator.get_tiers()
    print tiers
    assert len(tiers) == 2
    decorator.TEST_TIERS = dtt


def test_specifictype():
    """
    Test to make sure that the decorator module can return a test of a
    specific type.
    """

    dtt = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)

    tests = list(decorator.get_tests(2, 1))
    assert len(tests) == 2
    decorator.TEST_TIERS = dtt


def test_assumedtype():
    """
    Test to see if the decorator module can find tests for generic as well as
    specific types.
    """

    dtt = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    decorator.register_test(tier=1)(lambda: None)
    decorator.register_test(tier=2, expected_type=5)(lambda: None)
    decorator.register_test(tier=2)(lambda: None)
    decorator.register_test(tier=2, simple=True)(lambda: None)

    tests = list(decorator.get_tests(2, 5))
    assert len(tests) == 3
    decorator.TEST_TIERS = dtt


def test_version_range():
    """
    Tests that the appropriate versions after the specified versions are
    returned.
    """

    new_versions = {'1': {'guid': 'foo',
                          'versions': map(str, range(10))}}
    eq_(decorator.version_range('foo', '8', app_versions=new_versions),
        ['8', '9'])
    eq_(decorator.version_range('foo', '5', app_versions=new_versions),
        ['5', '6', '7', '8', '9'])


def test_version_range_before():
    """Test the `before` parameter of version_range."""

    new_versions = {'1': {'guid': 'foo',
                          'versions': map(str, range(10))}}

    eq_(decorator.version_range('foo', '5', '6', app_versions=new_versions),
        ['5'])
    eq_(decorator.version_range('foo', '8', '50', app_versions=new_versions),
        ['8', '9'])

