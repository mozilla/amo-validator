from nose.tools import eq_

from validator.chromemanifest import ChromeManifest


def test_open():
    """Open a chrome file and ensure that data can be pulled from it."""

    chrome = open("tests/resources/chromemanifest/chrome.manifest")
    chrome_data = chrome.read()

    manifest = ChromeManifest(chrome_data, "chrome.manifest")
    assert manifest is not None

    assert manifest.get_value("locale", "basta")["object"] == "resource"

    g_obj = list(manifest.get_objects("subject", "predicate"))

    assert len(g_obj) == 1
    assert g_obj[0] == "object"

    obj_resource = list(manifest.get_triples(None, None, "resource"))
    assert len(obj_resource) == 2

    pred_pred = list(manifest.get_triples(None, "predicate", None))
    assert len(pred_pred) == 2

    sub_locale = list(manifest.get_triples("locale", None, None))
    assert len(sub_locale) == 2


def test_lines():
    """Test that the correct line numbers are given in a chrome.manifest."""

    c = ChromeManifest("""
    zero foo bar
    one bar foo
    two abc def
    #comment
    four def abc
    """.strip(), "chrome.manifest")

    eq_(list(c.get_triples(subject="zero"))[0]["line"], 1)
    eq_(list(c.get_triples(subject="one"))[0]["line"], 2)
    eq_(list(c.get_triples(subject="two"))[0]["line"], 3)
    eq_(list(c.get_triples(subject="four"))[0]["line"], 5)


def test_incomplete_triplets():
    """Test that incomplete triplets are ignored."""

    c = ChromeManifest("foo\nbar", "chrome.manifest")
    assert not c.triples


def test_duplicate_subjects():
    """Test that two triplets with the same subject can be retrieved."""

    c = ChromeManifest("""
    foo bar abc
    foo bar def
    foo bam test
    oof rab cba
    """, "chrome.manifest")

    assert len(list(c.get_triples(subject="foo"))) == 3
    assert len(list(c.get_triples(subject="foo", predicate="bar"))) == 2
    assert len(list(c.get_triples(subject="foo",
                                  predicate="bar",
                                  object_="abc"))) == 1


def test_applicable_overlays():
    """
    Test that overlays that apply to the current chrome context are returned
    with proper paths.
    """

    c = ChromeManifest("""
    content ns1 jar:foo.jar!/content/junk/
    content ns1 jar:bar.jar!/content/stuff/
    content ns2 jar:zap.jar!/
    content ns3 /baz/

    overlay chrome://foo.xul chrome://ns1/content/junk/o1.xul
    overlay chrome://foo.xul chrome://ns1/content/junk/o2.xul
    overlay chrome://foo.xul chrome://ns1/content/stuff/o3.xul
    overlay chrome://foo.xul chrome://ns2/content/dir/o4.xul
    overlay chrome://foo.xul chrome://ns3/content/root/dir/o5.xul
    overlay chrome://foo.xul chrome://ns1/content/invalid/o6.xul
    """, "chrome.manifest")

    gac = c.get_applicable_overlays

    eq_(gac(MockPackStack()), set(["/baz/root/dir/o5.xul"]))
    eq_(gac(MockPackStack(["foo.jar"])), set(["/o1.xul", "/o2.xul"]))
    eq_(gac(MockPackStack(["bar.jar"])), set(["/o3.xul"]))
    eq_(gac(MockPackStack(["zap.jar"])), set(["/content/dir/o4.xul"]))


def test_reverse_lookup():
    """Test that the chrome reverse lookup function works properly."""

    c = ChromeManifest("""
    content ns1 /dir1/
    content ns2 /dir2/foo/
    content nsbad1 /dir3
    content ns3 jar:foo.jar!/subdir1/
    content ns3 jar:zap.jar!/altdir1/
    content ns4 jar:bar.jar!/subdir2
    """, "chrome.manifest")

    eq_(c.reverse_lookup(MockPackStack(), "random.js"), None)
    eq_(c.reverse_lookup(MockPackStack(), "/dir1/x.js"),
        "chrome://ns1/x.js")
    eq_(c.reverse_lookup(MockPackStack(), "/dir2/x.js"), None)
    eq_(c.reverse_lookup(MockPackStack(), "/dir2/foo/x.js"),
        "chrome://ns2/x.js")
    eq_(c.reverse_lookup(MockPackStack(), "/dir3/x.js"),
        "chrome://nsbad1/x.js")
    eq_(c.reverse_lookup(MockPackStack(["foo.jar"]), "/x.js"),
        "chrome://ns3/subdir1/x.js")
    eq_(c.reverse_lookup(MockPackStack(["foo.jar"]), "/zap/x.js"),
        "chrome://ns3/subdir1/zap/x.js")
    eq_(c.reverse_lookup(MockPackStack(["bar.jar"]), "/x.js"),
        "chrome://ns4/subdir2/x.js")
    eq_(c.reverse_lookup(MockPackStack(["zap.jar"]), "/x.js"),
        "chrome://ns3/altdir1/x.js")


class MockPackStack(object):

    def __init__(self, stack=None):
        if stack is None:
            stack = []
        self.package_stack = stack

    def is_nested_package(self):
        return bool(self.package_stack)

