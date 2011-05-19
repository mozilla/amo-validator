from validator.chromemanifest import ChromeManifest


def test_open():
    """Open a chrome file and ensure that data can be pulled from it."""

    chrome = open("tests/resources/chromemanifest/chrome.manifest")
    chrome_data = chrome.read()

    manifest = ChromeManifest(chrome_data)
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

    c = ChromeManifest("""zero foo bar
one bar foo
two abc def
#comment
four def abc""")

    assert list(c.get_triples(subject="zero"))[0]["line"] == 1
    assert list(c.get_triples(subject="one"))[0]["line"] == 2
    assert list(c.get_triples(subject="two"))[0]["line"] == 3
    assert list(c.get_triples(subject="four"))[0]["line"] == 5


def test_incomplete_triplets():
    """Test that incomplete triplets are ignored."""

    c = ChromeManifest("foo\nbar")
    assert not c.triples


def test_duplicate_subjects():
    """Test that two triplets with the same subject can be retrieved."""

    c = ChromeManifest("""
foo bar abc
foo bar def
foo bam test
oof rab cba
""")

    assert len(list(c.get_triples(subject="foo"))) == 3
    assert len(list(c.get_triples(subject="foo", predicate="bar"))) == 2
    assert len(list(c.get_triples(subject="foo",
                                  predicate="bar",
                                  object_="abc"))) == 1

