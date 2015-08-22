import types
from StringIO import StringIO
from validator.contextgenerator import ContextGenerator

try:
    from html.parser import HTMLParser, HTMLParseError
except ImportError:
    from HTMLParser import HTMLParser, HTMLParseError


class DTDParser(object):
    'Parses and serializes DTD files. This is useful for L10n tests.'

    def __init__(self, dtd):
        """
        Creation of DTD parsers can be done based on a local file
        (provided as a string to the path), or directly (in memory as a
        StringIO object).
        """

        self.entities = {}
        self.items = []

        data = ''
        if isinstance(dtd, types.StringTypes):
            with open(dtd) as dtd_instance:
                data = dtd_instance.read()
        elif isinstance(dtd, file):
            data = dtd.read()
        elif isinstance(dtd, StringIO):
            data = dtd.getvalue()

        self._parse(data)

        # Create a context for the file
        self.context = ContextGenerator(data)

    def __len__(self):
        return len(self.entities)

    def _parse(self, data):
        'Parses the DTD data and stores it in an aggregate format.'

        parser = DTDXMLParser()
        # Feed the DTD file in line-by-line.
        for split_line in data.split('\n'):
            try:
                parser.feed(split_line + '\n')
            except HTMLParseError:
                parser = DTDXMLParser()
            else:
                if parser.out_buffer:
                    for name, value, line in parser.out_buffer:
                        self.entities[name] = value
                        self.items.append((name, value, line))
                    parser.clear_buffer()


class DTDXMLParser(HTMLParser):
    'Parses the individual XML entities in a DTD document.'

    def __init__(self):
        HTMLParser.__init__(self)
        self.out_buffer = []

    # Support for py2.7/3k
    def handle_comment(self, data):
        self.unknown_decl(data)

    def unknown_decl(self, decl):
        'Handles non-DOCTYPE SGML declarations in *ML documents.'

        decl = decl.strip()
        split_decl = decl.split()

        if len(split_decl) < 3 or split_decl[0] != 'ENTITY':
            # Interestingly enough, it legitimately IS an unknown
            # declaration. Funny thing, you know?
            return

        self.out_buffer.append((split_decl[1],
                                split_decl[2].strip('\'"'),
                                self.getpos()[0]))  # Pos 0 is the line no.

    def clear_buffer(self):
        'Clears the return buffer.'
        self.out_buffer = []
