import codecs
import textfilter

# Many thanks to nmaier for inspiration and code in this module

UNICODES = [
    (codecs.BOM_UTF8, "utf-8"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    ]

COMMON_ENCODINGS = ("utf-16", "latin_1", "ascii")

def decode(data):
    """
    Decode data employing some charset detection and including unicode BOM
    stripping.
    """

    # Don't make more work than we have to.
    if not isinstance(data, str):
        return data

    # Detect standard unicodes.
    for bom, encoding in UNICODES:
        if data.startswith(bom):
            return unicode(data[len(bom):], encoding, "ignore")

    # Try straight UTF-8
    try:
        return unicode(data, "utf-8")
    except UnicodeDecodeError:
        pass

    # Test for latin_1, because it can be matched as UTF-16
    # Somewhat of a hack, but it works and is about a thousand times faster
    # than using chardet.
    if all(ord(c) < 256 for c in data):
        try:
            return unicode(data, "latin_1")
        except UnicodeDecodeError:
            pass

    # Test for various common encodings.
    for encoding in COMMON_ENCODINGS:
        try:
            return unicode(data, encoding)
        except UnicodeDecodeError:
            pass

    # Anything else gets filtered.
    return unicode(textfilter.filter_ascii(data), errors="replace")

