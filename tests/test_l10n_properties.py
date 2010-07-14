import os

from StringIO import StringIO

import validator.testcases.l10n.properties as properties

def test_passing_file():
    "Tests a valid properties file by passing in a file path."
    
    path = "tests/resources/l10n/properties/valid.properties"
    parser = properties.PropertiesParser(path)
    
    _inspect_file_results(parser)
    

def test_passing_stream():
    "Tests a valid DTD file by passing in a data stream."
    
    path = "tests/resources/l10n/properties/valid.properties"
    file_ = open(path)
    data = file_.read()
    file_.close()
    parser = properties.PropertiesParser(StringIO(data))
    
    _inspect_file_results(parser)
    

def test_malformed_file():
    """Tests a properties file that contains non-comment,
    non-whitespace lines without a distinct value."""
    
    path = "tests/resources/l10n/properties/extra_breaks.properties"
    parser = properties.PropertiesParser(path)
    assert len(parser) == 2
    assert parser.entities["foo"] == "bar"
    assert parser.entities["abc.def"] == "xyz"
    

def _inspect_file_results(parser):
    "Inspects the output of the properties file tests."
    
    assert len(parser) == 7
    assert "foo" in parser.entities
    assert parser.entities["foo"] == "bar"
    assert "overwrite" in parser.entities
    assert parser.entities["overwrite"] == "bar"
    assert "two" in parser.entities
    assert parser.entities["two"] == "per"
    assert "line" in parser.entities
    assert parser.entities["line"] == "woot"
    
