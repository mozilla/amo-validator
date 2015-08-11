import mock
import time

from nose.tools import eq_

from validator import submain
from validator.chromemanifest import ChromeManifest
from validator.errorbundler import ErrorBundle
from .helper import MockXPI


@mock.patch('validator.submain.test_package')
def test_prepare_package(test_package):
    """Tests that the prepare_package does not raise any errors when given
    a valid add-on."""

    err = ErrorBundle()
    submain.prepare_package(err, 'tests/resources/main/foo.xpi')
    assert not err.failed()


@mock.patch('validator.submain.test_package')
def test_validation_timeout(test_package):
    def slow(*args, **kw):
        time.sleep(1)
    test_package.side_effect = slow

    err = ErrorBundle()
    err.error(('an', 'error'), 'occurred')

    submain.prepare_package(err, 'tests/resources/main/foo.xpi', timeout=0.1)

    # Make sure that our error got moved to the front of the list.
    eq_(len(err.errors), 2)
    eq_(err.errors[0]['id'],
        ('validator', 'unexpected_exception', 'validation_timeout'))


@mock.patch('validator.submain.test_package')
@mock.patch('validator.errorbundler.log')
def test_validation_error(log, test_package):
    """Test that an unexpected exception during validation is turned into
    an error message and logged."""

    test_package.side_effect = Exception

    err = ErrorBundle()
    err.error(('an', 'error'), 'occurred')

    submain.prepare_package(err, 'tests/resources/main/foo.xpi')

    assert log.error.called

    # Make sure that our error got moved to the front of the list.
    eq_(len(err.errors), 2)
    eq_(err.errors[0]['id'], ('validator', 'unexpected_exception'))


@mock.patch('validator.submain.test_search')
def test_prepare_package_extension(test_search):
    'Tests that bad extensions get outright rejections.'

    # Files with an invalid extension raise an error prior to
    # calling `test_search`.
    err = ErrorBundle()
    submain.prepare_package(err, 'foo/bar/test.foo')

    assert not test_search.called

    eq_(len(err.errors), 1)
    eq_(err.errors[0]['id'], ('main', 'prepare_package', 'not_found'))

    # Files which do not exist raise an error prior to calling `test_search`.
    err = ErrorBundle()
    submain.prepare_package(err, 'foo/bar/test.xml')

    assert not test_search.called
    eq_(len(err.errors), 1)
    eq_(err.errors[0]['id'], ('main', 'prepare_package', 'not_found'))


def test_prepare_package_missing():
    'Tests that the prepare_package function fails when file is not found'

    err = ErrorBundle()
    submain.prepare_package(err, 'foo/bar/asdf/qwerty.xyz')

    assert err.failed()


def test_prepare_package_bad_file():
    'Tests that the prepare_package function fails for unknown files'

    err = ErrorBundle()
    submain.prepare_package(err, 'tests/resources/main/foo.bar')

    assert err.failed()


@mock.patch('validator.submain.test_search')
def test_prepare_package_xml(test_search):
    'Tests that the prepare_package function passes with search providers'

    err = ErrorBundle()
    submain.prepare_package(err, 'tests/resources/main/foo.xml')

    assert not err.failed()
    assert test_search.called

    test_search.side_effect = lambda err, *args: err.error(('x'), 'Failed')
    submain.prepare_package(err, 'tests/resources/main/foo.xml')

    assert err.failed()


# Test the function of the decorator iterator

def test_test_inner_package():
    'Tests that the test_inner_package function works properly'

    with patch_decorator():
        err = MockErrorHandler()

        submain.test_inner_package(err, 'foo', 'bar')

        assert not err.failed()


def test_test_inner_package_failtier():
    'Tests that the test_inner_package function fails at a failed tier'

    with patch_decorator(fail_tier=3):
        err = MockErrorHandler()

        submain.test_inner_package(err, 'foo', 'bar')

        assert err.failed()


# Test chrome.manifest populator
def test_populate_chrome_manifest():
    """Ensure that the chrome manifest is populated if available."""

    err = MockErrorHandler()
    package_contents = {
        'chrome.manifest': 'tests/resources/chromemanifest/chrome.manifest'}
    package = MockXPI(package_contents)

    submain.populate_chrome_manifest(err, MockXPI())
    assert not err.pushable_resources

    submain.populate_chrome_manifest(err, package)
    assert err.pushable_resources
    assert 'chrome.manifest' in err.pushable_resources
    print err.pushable_resources
    assert isinstance(err.pushable_resources['chrome.manifest'],
                      ChromeManifest)

    assert err.resources
    assert 'chrome.manifest_nopush' in err.resources
    print err.resources
    assert isinstance(err.resources['chrome.manifest_nopush'], ChromeManifest)


def test_proper_linked_manifest():
    """Test that linked manifests are imported properly."""

    err = ErrorBundle()
    package = MockXPI({
        'chrome.manifest': 'tests/resources/submain/linkman/base1.manifest',
        'submanifest.manifest':
            'tests/resources/submain/linkman/base2.manifest'})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource('chrome.manifest')
    assert chrome

    assert not err.failed() or err.notices

    # From the base file:
    assert list(chrome.get_triples(subject='foo'))
    # From the linked manifest:
    zaps = list(chrome.get_triples(subject='zap'))
    assert zaps
    eq_(zaps[0]['filename'], 'submanifest.manifest')
    eq_(zaps[0]['context'].data, ['zap baz', ''])


def test_proper_linked_manifest_relative():
    """
    Test that linked manifests are imported relatively when using relative
    paths.
    """

    err = ErrorBundle()
    package = MockXPI({
        'chrome.manifest': 'tests/resources/submain/linkman/subdir.manifest',
        'dir/level2.manifest':
            'tests/resources/submain/linkman/foosub.manifest',
        'dir/foo.manifest': 'tests/resources/submain/linkman/base2.manifest'})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource('chrome.manifest')
    assert chrome

    assert not err.failed() or err.notices

    # From the linked manifest:
    zaps = list(chrome.get_triples(subject='zap'))
    assert zaps
    eq_(zaps[0]['filename'], 'dir/foo.manifest')
    eq_(zaps[0]['context'].data, ['zap baz', ''])


def test_missing_manifest_link():
    """Test that missing linked manifests are properly flagged."""

    err = ErrorBundle()
    package = MockXPI({
        'chrome.manifest': 'tests/resources/submain/linkman/base1.manifest'})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource('chrome.manifest')
    assert chrome

    assert not err.failed()
    assert err.notices

    # From the base file:
    assert list(chrome.get_triples(subject='foo'))
    # From the linked manifest:
    assert not list(chrome.get_triples(subject='zap'))


def test_linked_manifest_recursion():
    """Test that recursive linked manifests are flagged properly."""

    err = ErrorBundle()
    package = MockXPI({
        'chrome.manifest': 'tests/resources/submain/linkman/base1.manifest',
        'submanifest.manifest':
            'tests/resources/submain/linkman/recurse.manifest'})

    submain.populate_chrome_manifest(err, package)
    chrome = err.get_resource('chrome.manifest')
    assert chrome

    print err.print_summary(verbose=True)

    assert err.failed()
    assert not err.notices

    # From the base file:
    assert list(chrome.get_triples(subject='foo'))
    # From the linked manifest:
    assert not list(chrome.get_triples(subject='zap'))


# Test determined modes
def test_test_inner_package_determined():
    'Tests that the determined test_inner_package function works properly'

    with patch_decorator(determined=True) as decorator:
        err = MockErrorHandler(determined=True)

        submain.test_inner_package(err, 'foo', 'bar')

        assert not err.failed()
        assert decorator.last_tier == 5


def test_test_inner_package_determined_failtier():
    'Tests the test_inner_package function in determined mode while failing'

    with patch_decorator(fail_tier=3, determined=True) as decorator:
        err = MockErrorHandler(determined=True)

        submain.test_inner_package(err, 'foo', 'bar')

        assert err.failed()
        assert decorator.last_tier == 5


# These desparately need to be rewritten:

def patch_decorator(*args, **kw):
    return mock.patch.object(submain, 'decorator', MockDecorator(*args, **kw))


class MockDecorator(mock.MagicMock):

    def __init__(self, fail_tier=None, determined=False, **kw):
        super(MockDecorator, self).__init__(**kw)

        self.determined = determined
        self.ordering = [1]
        self.fail_tier = fail_tier
        self.last_tier = 0

    def get_tiers(self):
        'Returns unordered tiers. These must be in a random order.'
        return (4, 1, 3, 5, 2)

    def get_tests(self, tier, type):
        'Should return a list of tests that occur in a certain order'

        self.on_tier = tier

        print 'Retrieving Tests: Tier %d' % tier

        if self.fail_tier is not None:
            if tier == self.fail_tier:
                print '> Fail Tier'

                yield {'test': lambda x, y: x.fail_tier(),
                       'simple': False,
                       'versions': None}

            assert tier <= self.fail_tier or self.determined

        self.last_tier = tier

        for x in range(1, 10):  # Ten times because we care
            # ^ Very witty. However, it would be nice to actually know
            # exactly why we're yielding these ten times.

            print 'Yielding Complex'
            yield {'test': lambda x, z: x.report(tier),
                   'simple': False,
                   'versions': None}
            print 'Yielding Simple'
            yield {'test': lambda x, z=None: x.test_simple(z),
                   'simple': True,
                   'versions': None}

    def report_tier(self, tier):
        'Checks to make sure the last test run is on the current tier.'

        assert tier == self.on_tier

    def report_fail(self):
        'Alerts the tester to a failure'

        print self.on_tier
        print self.fail_tier
        assert self.on_tier == self.fail_tier


class MockErrorHandler(mock.MagicMock):

    def __init__(self, determined=False, **kw):
        super(MockErrorHandler, self).__init__(**kw)

        self.detected_type = 0
        self.has_failed = False
        self.determined = determined

        self.pushable_resources = {}
        self.resources = {}

    def save_resource(self, name, value, pushable=False):
        'Saves a resource to the bundler'
        resources = self.pushable_resources if pushable else self.resources
        resources[name] = value

    def set_tier(self, tier):
        'Sets the tier'
        pass

    def report(self, tier):
        'Passes the tier back to the mock decorator to verify the tier'
        submain.decorator.report_tier(tier)

    def fail_tier(self):
        'Simulates a failure'
        self.has_failed = True
        submain.decorator.report_fail()

    def test_simple(self, z):
        'Makes sure that the second two params of a simple test are respected'
        assert z is None

    def failed(self, fail_on_warnings=False):
        'Simple accessor because the standard error handler has one'
        return self.has_failed
