from nose.tools import eq_

from validator.version import Version, VersionPart

def test_versionpart_stringify():
    """Tests that VersionPart objects stringify to their original string."""

    PART = "0b0b"
    eq_(str(VersionPart(PART)), PART)

def test_version_stringify():
    """Tests that Version objects stringify to their original string."""

    PART    = "0b0b"
    VERSION = ".".join((PART, PART, PART, PART))
    eq_(str(Version(VERSION)), VERSION)

def test_versionpart_eq():
    """Tests that VersionPart objects equal themselves."""

    PART = "0b0b"
    a = VersionPart(PART)
    b = VersionPart(PART)
    eq_(a, a)
    eq_(a, b)
    assert not (a < b)
    assert not (a > b)

def test_version_eq():
    """Tests that Version objects equal themselves."""

    PART    = "0b0b"
    VERSION = ".".join((PART, PART, PART, PART))
    a = Version(VERSION)
    b = Version(VERSION)
    eq_(a, a)
    eq_(a, b)
    assert not (a < b)
    assert not (a > b)

def test_nullstring_greater_than_string():
    """
    Tests that null strings in versions are greater than non-null
    strings.
    """

    assert VersionPart("1") > VersionPart("1a")
    assert VersionPart("1a1") > VersionPart("1a1a")

def test_number_part_comparison():
    """
    Tests that number comparisons work as expected in VersionParts.
    """

    assert VersionPart("1") < VersionPart("2")
    assert VersionPart("3") < VersionPart("20")

    assert VersionPart("a1") < VersionPart("a2")
    assert VersionPart("a3") < VersionPart("a20")

    assert VersionPart("1a1") < VersionPart("1a2")
    assert VersionPart("1a3") < VersionPart("1a20")

def test_number_part_comparison():
    """
    Tests that string comparisons work as expected in VersionParts.
    """

    assert VersionPart("a") < VersionPart("b")
    assert VersionPart("1a") < VersionPart("1b")
    assert VersionPart("1a1a") < VersionPart("1b1b")
    assert VersionPart("1a1a20") < VersionPart("1b1b3")

def test_nullpart_less_than_part():
    """
    Tests that null version parts in versions are less than non-null
    parts.
    """

    assert Version("1") < Version("1.0")

def test_greater_part():
    """
    Tests that a greater VersionPart works as expected in Version
    comparisons.
    """

    assert VersionPart("1") < VersionPart("2")
    assert Version("1.1") < Version("1.2")

def test_asterisk_greater_than_charcode():
    """
    '*' is greater than any other value in version parts. Test that
    it is greater than a character with a greater charcode than
    itself.
    """

    assert "," > "*"
    assert VersionPart("*") > VersionPart(",")

def test_magical_plus_equals_plusone_pre_nonsense():
    """
    Test that the magical behavior where 1+ == 2pre is preserved.
    """

    eq_(VersionPart("1+"), VersionPart("2pre"))
