import validator.testcases.l10n.dtd as dtd


def test_passing_file():
    """Test a valid DTD file by passing in a file path."""

    path = "tests/resources/l10n/dtd/valid.dtd"
    parser = dtd.DTDParser(path)

    _inspect_file_results(parser)


def test_passing_stream():
    """Test a valid DTD file by passing in a data stream."""

    path = "tests/resources/l10n/dtd/valid.dtd"
    parser = dtd.DTDParser(open(path))
    _inspect_file_results(parser)


def test_shady_file():
    """
    Test a somewhat silly DTD file that has excessive line breaks. This
    emulates the mozilla.dtd file in the reference packs.
    """

    path = "tests/resources/l10n/dtd/extra_breaks.dtd"
    parser = dtd.DTDParser(path)

    _inspect_file_results(parser)


def test_broken_file():
    """
    Tests a DTD file that has malformed content to make sure invalid tags are
    ignored. Also, non-ENTITY declarations should be ignored.
    """

    path = "tests/resources/l10n/dtd/malformed.dtd"
    parser = dtd.DTDParser(path)

    _inspect_file_results(parser)


def _inspect_file_results(parser):
    """Inspect the output of the DTD file tests."""

    assert len(parser) == 7
    assert "foo" in parser.entities
    assert parser.entities["foo"] == "bar"
    assert "overwrite" in parser.entities
    assert parser.entities["overwrite"] == "bar"
    assert "two" in parser.entities
    assert parser.entities["two"] == "per"
    assert "line" in parser.entities
    assert parser.entities["line"] == "woot"

