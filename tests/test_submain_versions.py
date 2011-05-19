import validator.submain
from validator import decorator
from validator.errorbundler import ErrorBundle


def test_version_decorators_accepted():
    """
    Test that decorators that specify versions to target accept the proper
    add-ons for testing.
    """

    err = ErrorBundle()
    err.save_resource("supported_versions", {"firefox": ["1.2.3"]})

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, package, xpi):
        print "Ran test"
        err.save_resource("executed", True)

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, {}, None)

    assert err.get_resource("executed")
    decorator.TEST_TIERS = tests


def test_version_decorators_denied_guid():
    """
    Test that decorators that specify versions to target deny add-ons that do
    not support the particular app being tested.
    """

    err = ErrorBundle()
    err.save_resource("supported_versions", {"firefox": ["1.2.3"]})

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"foobarfox": ["1.0.0",
                                                             "1.2.3"]})
    def version_test(err, package, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, {}, None)
    decorator.TEST_TIERS = tests


def test_version_decorators_denied_version():
    """
    Test that decorators that specify versions to target deny add-ons that do
    not support the particular app version being tested for.
    """

    err = ErrorBundle()
    err.save_resource("supported_versions", {"firefox": ["1.2.3"]})

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "2.0.0"]})
    def version_test(err, package, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, {}, None)
    decorator.TEST_TIERS = tests


def test_version_forappversions_accepted():
    """
    Test that for_appversions targets application versions properly.
    """

    err = ErrorBundle()
    err.save_resource("supported_versions", {"firefox": ["1.2.3"]})

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, package, xpi):
        print "Ran test"
        err.save_resource("executed", True)

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, {}, None,
                                         for_appversions={"firefox":
                                                              ["1.2.3"]})

    assert err.get_resource("executed")
    decorator.TEST_TIERS = tests


def test_version_forappversions_denied():
    """
    Test that for_appversions denies target application versions properly.
    """

    err = ErrorBundle()
    err.save_resource("supported_versions", {"firefox": ["1.2.3"]})

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, package, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, {}, None,
                                         for_appversions={"thunderbird":
                                                              ["1.2.3"]})

    assert not err.get_resource("executed")
    decorator.TEST_TIERS = tests

