from StringIO import StringIO
import validator.rdf as rdf
from validator.rdf import RDFParser


def testopen():
    """Tests that the RDF parser is capable of loading an RDF file
    successfully."""

    r = RDFParser(open("tests/resources/rdf/pass.rdf"))
    assert r.rdf

def test_load_bad():
    """Tests that the RDF parser throws an error for invalid, damaged,
    or corrupt RDF files."""

    r = RDFParser(open("tests/resources/rdf/fail.rdf"))
    assert not r.rdf

def test_load_rdf_stringio():
    """Tests that the RDF parser is capable of loading an RDF file
    from a StringIO object successfully."""

    sio = StringIO(open("tests/resources/rdf/pass.rdf").read())
    r = RDFParser(sio)
    assert r.rdf

def test_namespacing():
    """Tests that the RDF parser successfully creates namespaces."""

    r = RDFParser(open("tests/resources/rdf/pass.rdf"), "foo")

    assert r.namespace == "foo"
    assert str(r.uri("bar")) == "foo#bar"
    assert str(r.uri("bar", "abc")) == "abc#bar"

def test_namespacing():
    """Tests that the RDF parser successfully creates namespaces."""

    r = RDFParser(open("tests/resources/rdf/pass.rdf"), "foo")

    assert r.namespace == "foo"
    assert str(r.uri("bar")) == "foo#bar"
    assert str(r.uri("bar", "abc")) == "abc#bar"

def test_get_root_subject():
    "Tests the integrity of the get_root_subject() function"

    r = RDFParser(open("tests/resources/rdf/pass.rdf"))
    type_uri = r.uri("type")

    emtype = r.get_object(None, type_uri)
    assert emtype is not None

    emtype = r.get_object(r.get_root_subject(), type_uri)
    assert emtype is not None

def test_get_object():
    """"Tests the integrity of the get_object() and get_objects()
    functions."""

    r = RDFParser(open("tests/resources/rdf/pass.rdf"))
    test_uri = r.uri("test")

    emtest = r.get_object(None, test_uri)
    assert emtest is not None

    emtests = r.get_objects(None, test_uri)
    assert len(emtests) == 3
    assert emtests[0] == emtest

