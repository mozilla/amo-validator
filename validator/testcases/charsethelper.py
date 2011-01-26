import chardet
import codecs

UNICODES = [
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    (codecs.BOM_UTF8, "utf-8")
    ]

def decode(data, encoding="utf-8"):
    "Decode data employing some character set detection and including unicode BOM stripping"

    # try the unicodes by BOM detection
    # strip the BOM in the process
    head = data[:4]
    for testhead,encoding in UNICODES:
        if head.startswith(testhead):
            return unicode(data[len(testhead):], encoding, "ignore")

    # utf-8 is pretty common (without BOM)
    try:
        return unicode(data, "utf-8")
    except UnicodeError:
        pass

    # try chardet detection
    try:
        detected = chardet.detect(data)
        return unicode(data, detected["encoding"])
    except:
        pass

    # try other encodings
    for encoding in ("ascii", "latin_1"):
        try:
            return unicode(data, encoding)
        except UnicodeError:
            pass

    # last resort; try plain unicode without a charset
    return unicode(data)
