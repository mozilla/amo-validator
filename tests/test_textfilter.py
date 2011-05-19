import validator.textfilter as textfilter


def test_is_ctrl_char():
    "Tests whether a character is a control character"

    for i in range(0, 127):
        result = textfilter.is_ctrl_char(chr(i))
        assert (i < 32 and i not in (9, 10, 13)) == result

    # Test ordinal override
    assert not textfilter.is_ctrl_char(chr(3), 50)


def test_is_standard_ascii():
    "Tests the is_standard_ascii function"

    assert not textfilter.is_standard_ascii(chr(3))
    assert textfilter.is_standard_ascii(chr(9))
    assert not textfilter.is_standard_ascii(chr(127))
    assert not textfilter.is_standard_ascii(chr(200))


def test_filter_ascii():
    "Tests the filter_ascii function"

    assert not textfilter.filter_ascii("".join([chr(x) for
                                                x in
                                                range(9)])
                                        ).replace("?","")
    assert not any(x.replace("?", "") for
                   x in
                   textfilter.filter_ascii([chr(x) for x in range(9)]))

