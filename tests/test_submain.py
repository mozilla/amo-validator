import time

from nose.tools import raises

import validator.submain as submain
from validator.errorbundler import ErrorBundle
from validator.chromemanifest import ChromeManifest
from validator.constants import *
from helper import MockXPI


def test_prepare_package():
    "Tests that the prepare_package function passes for valid data"

    tp = submain.test_package
    submain.test_package = lambda w, x, y, z, for_appversions: True

    err = ErrorBundle()
    assert submain.prepare_package(err, "tests/resources/main/foo.xpi") == True
    submain.test_package = tp


@raises(RuntimeError)
def test_validation_timeout():
    tp = submain.test_package
    def slow(*args, **kw):
        time.sleep(1)
    submain.test_package = slow
    try:
        err = ErrorBundle()
        submain.prepare_package(err, "tests/resources/main/foo.xpi",
                                timeout=0.1)
    finally:
        submain.test_package = tp


def test_prepare_package_extension():
    "Tests that bad extensions get outright rejections"

    assert submain.prepare_package(None, "foo/bar/test.foo") == False

    ts = submain.test_search
    submain.test_search = lambda x, y, z: True
    assert submain.prepare_package(None, "foo/bar/test.xml") == True
    submain.test_search = ts


def test_prepare_package_missing():
    "Tests that the prepare_package function fails when file is not found"

    err = ErrorBundle()
    submain.prepare_package(err, "foo/bar/asdf/qwerty.xyz")

    assert err.failed()


def test_prepare_package_bad_file():
    "Tests that the prepare_package function fails for unknown files"

    err = ErrorBundle()
    submain.prepare_package(err, "tests/resources/main/foo.bar")

    assert err.failed()


def test_prepare_package_xml():
    "Tests that the prepare_package function passes with search providers"

    smts = submain.test_search
    submain.test_search = lambda err, y, z: True

    err = ErrorBundle()
    submain.prepare_package(err, "tests/resources/main/foo.xml")

    assert not err.failed()

    submain.test_search = lambda err, y, z: err.error(("x"), "Failed")
    submain.prepare_package(err, "tests/resources/main/foo.xml")

    assert err.failed()
    submain.test_search = smts

# Test the function of the decorator iterator

def test_test_inner_package():
    "Tests that the test_inner_package function works properly"

    smd = submain.decorator
    decorator = MockDecorator()
    submain.decorator = decorator
    err = MockErrorHandler(decorator)

    submain.test_inner_package(err, "foo", "bar")

    assert not err.failed()
    submain.decorator = smd


def test_test_inner_package_failtier():
    "Tests that the test_inner_package function fails at a failed tier"

    smd = submain.decorator
    decorator = MockDecorator(3)
    submain.decorator = decorator
    err = MockErrorHandler(decorator)

    submain.test_inner_package(err, "foo", "bar")

    assert err.failed()
    submain.decorator = smd


# Test chrome.manifest populator
def test_populate_chrome_manifest():
    """Ensure that the chrome manifest is populated if available."""

    err = MockErrorHandler(None)
    package_contents = {"chrome.manifest":
            "tests/resources/chromemanifest/chrome.manifest"}
    package = MockXPI(package_contents)

    submain.populate_chrome_manifest(err, MockXPI())
    assert not err.pushable_resources

    submain.populate_chrome_manifest(err, package)
    assert err.pushable_resources
    assert "chrome.manifest" in err.pushable_resources
    print err.pushable_resources
    assert isinstance(err.pushable_resources["chrome.manifest"],
                      ChromeManifest)

    assert err.resources
    assert "chrome.manifest_nopush" in err.resources
    print err.resources
    assert isinstance(err.resources["chrome.manifest_nopush"], ChromeManifest)


def test_proper_linked_manifest():
    """Test that linked manifests are imported properly."""

    err = ErrorBundle()
    package = MockXPI({
        "chrome.manifest": "tests/resources/submain/linkman/base1.manifest",
        "submanifest.manifest":
            "tests/resources/submain/linkman/base2.manifest"})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource("chrome.manifest")
    assert chrome

    assert not err.failed() or err.notices

    # From the base file:
    assert list(chrome.get_triples(subject="foo"))
    # From the linked manifest:
    assert list(chrome.get_triples(subject="zap"))


def test_missing_manifest_link():
    """Test that missing linked manifests are properly flagged."""

    err = ErrorBundle()
    package = MockXPI({
        "chrome.manifest": "tests/resources/submain/linkman/base1.manifest"})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource("chrome.manifest")
    assert chrome

    assert not err.failed()
    assert err.notices

    # From the base file:
    assert list(chrome.get_triples(subject="foo"))
    # From the linked manifest:
    assert not list(chrome.get_triples(subject="zap"))


def test_linked_manifest_recursion():
    """Test that recursive linked manifests are flagged properly."""

    err = ErrorBundle()
    package = MockXPI({
        "chrome.manifest": "tests/resources/submain/linkman/base1.manifest",
        "submanifest.manifest":
            "tests/resources/submain/linkman/recurse.manifest"})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource("chrome.manifest")
    assert chrome

    assert err.failed()
    assert not err.notices

    # From the base file:
    assert list(chrome.get_triples(subject="foo"))
    # From the linked manifest:
    assert not list(chrome.get_triples(subject="zap"))


# Test determined modes
def test_test_inner_package_determined():
    "Tests that the determined test_inner_package function works properly"

    smd = submain.decorator
    decorator = MockDecorator(None, True)
    submain.decorator = decorator
    err = MockErrorHandler(decorator, True)

    submain.test_inner_package(err, "foo", "bar")

    assert not err.failed()
    assert decorator.last_tier == 5
    submain.decorator = smd


def test_test_inner_package_failtier():
    "Tests the test_inner_package function in determined mode while failing"

    smd = submain.decorator
    decorator = MockDecorator(3, True)
    submain.decorator = decorator
    err = MockErrorHandler(decorator, True)

    submain.test_inner_package(err, "foo", "bar")

    assert err.failed()
    assert decorator.last_tier == 5
    submain.decorator = smd


class MockDecorator:

    def __init__(self, fail_tier=None, determined=False):
        self.determined = determined
        self.ordering = [1]
        self.fail_tier = fail_tier
        self.last_tier = 0

    def get_tiers(self):
        "Returns unordered tiers. These must be in a random order."
        return (4, 1, 3, 5, 2)

    def get_tests(self, tier, type):
        "Should return a list of tests that occur in a certain order"

        self.on_tier = tier

        print "Retrieving Tests: Tier %d" % tier

        if self.fail_tier is not None:
            if tier == self.fail_tier:
                print "> Fail Tier"

                yield {"test": lambda x, y: x.fail_tier(),
                       "simple": False,
                       "versions": None}

            assert tier <= self.fail_tier or self.determined

        self.last_tier = tier

        for x in range(1,10): # Ten times because we care
            print "Yielding Complex"
            yield {"test": lambda x, z: x.report(tier),
                   "simple": False,
                   "versions": None}
            print "Yielding Simple"
            yield {"test": lambda x, z=None: x.test_simple(z),
                   "simple": True,
                   "versions": None}

    def report_tier(self, tier):
        "Checks to make sure the last test run is on the current tier."

        assert tier == self.on_tier

    def report_fail(self):
        "Alerts the tester to a failure"

        print self.on_tier
        print self.fail_tier
        assert self.on_tier == self.fail_tier


class MockErrorHandler:

    def __init__(self, mock_decorator, determined=False):
        self.decorator = mock_decorator
        self.detected_type = 0
        self.has_failed = False
        self.determined = determined

        self.pushable_resources = {}
        self.resources = {}

    def save_resource(self, name, value, pushable=False):
        "Saves a resource to the bundler"
        resources = self.pushable_resources if pushable else self.resources
        resources[name] = value

    def set_tier(self, tier):
        "Sets the tier"
        pass

    def report(self, tier):
        "Passes the tier back to the mock decorator to verify the tier"
        self.decorator.report_tier(tier)

    def fail_tier(self):
        "Simulates a failure"
        self.has_failed = True
        self.decorator.report_fail()

    def test_simple(self, z):
        "Makes sure that the second two params of a simple test are respected"
        assert z is None

    def failed(self, fail_on_warnings=False):
        "Simple accessor because the standard error handler has one"
        return self.has_failed

