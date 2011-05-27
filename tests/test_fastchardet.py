import fastchardet


def test_ascii():
    """Determines that fastchardet detects ASCII properly."""
    assert fastchardet.detect("This is plain ASCII")["encoding"] == "ascii"


def test_utf8():
    """Determine that fastchardet properly detects UTF-8."""

    assert fastchardet.detect("""\xEF\xBB\xBF
            Haldo, UTF-8
            """)["encoding"] == "utf_8"


def test_utfn():
    """Determine that fastchardet properly detects UTF-N."""

    assert fastchardet.detect("""\xFF\xFE\x00\x00
            Haldo, UTF-Not 8
            """)["encoding"] == "utf_n"


def test_unicode():
    """
    Make sure that things turn out right when we're silly sallies and pass
    unicode in.
    """

    assert fastchardet.detect(unicode("foo"))["encoding"] == "unicode"


def test_esoteric():
    """Make sure that fastchardet can detect other encodings."""

    a = lambda code: fastchardet.detect(code)["encoding"]

    # High Bytes
    print a("High Byte:\x91")
    assert a("High Byte:\x91") == "windows-1252"

    # UTF-8 without BOM
    print a("\xc2\xbc + \xc2\xbd = \xcd\xbe")
    assert a("\xc2\xbc + \xc2\xbd = \xcd\xbe") == "utf_8"

