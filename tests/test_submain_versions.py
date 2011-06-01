import validator.decorator
import validator.submain
from validator import decorator
from validator.errorbundler import ErrorBundle


class MockXPI:
    def __iter__(self):
        files = range(4)
        def i():
            for f in files:
                yield "file%d.foo" % f
        return i()

    def __contains__(self, item):
        return False


def test_version_decorators_accepted():
    """
    Test that decorators that specify versions to target accept the proper
    add-ons for testing.
    """

    err = ErrorBundle()
    err.supported_versions = {"firefox": ["1.2.3"]}

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, xpi):
        print "Ran test"
        err.save_resource("executed", True)

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, MockXPI())

    assert err.get_resource("executed")
    decorator.TEST_TIERS = tests


def test_version_decorators_denied_guid():
    """
    Test that decorators that specify versions to target deny add-ons that do
    not support the particular app being tested.
    """

    err = ErrorBundle()
    err.supported_versions = {"firefox": ["1.2.3"]}

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"foobarfox": ["1.0.0",
                                                             "1.2.3"]})
    def version_test(err, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, MockXPI())
    decorator.TEST_TIERS = tests


def test_version_decorators_denied_version():
    """
    Test that decorators that specify versions to target deny add-ons that do
    not support the particular app version being tested for.
    """

    err = ErrorBundle()
    err.supported_versions = {"firefox": ["1.2.3"]}

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "2.0.0"]})
    def version_test(err, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, MockXPI())
    decorator.TEST_TIERS = tests


def test_version_forappversions_accepted():
    """
    Test that for_appversions targets application versions properly.
    """

    err = ErrorBundle()
    err.supported_versions = {"firefox": ["1.2.3"]}

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, xpi):
        print "Ran test"
        err.save_resource("executed", True)

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, MockXPI(),
                                         for_appversions={"firefox":
                                                              ["1.2.3"]})

    assert err.get_resource("executed")
    decorator.TEST_TIERS = tests


def test_version_forappversions_denied():
    """
    Test that for_appversions denies target application versions properly.
    """

    err = ErrorBundle()
    err.supported_versions = {"firefox": ["1.2.3"]}

    tests = decorator.TEST_TIERS
    decorator.TEST_TIERS = {}

    @decorator.register_test(tier=5, versions={"firefox": ["1.0.0",
                                                           "1.2.3"]})
    def version_test(err, xpi):
        raise Exception("Should not have run!")

    print decorator.TEST_TIERS

    validator.submain.test_inner_package(err, MockXPI(),
                                         for_appversions={"thunderbird":
                                                              ["1.2.3"]})

    assert not err.get_resource("executed")
    decorator.TEST_TIERS = tests

