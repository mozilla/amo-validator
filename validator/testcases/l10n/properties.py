import types
from StringIO import StringIO
from validator.contextgenerator import ContextGenerator


class PropertiesParser(object):
    """
    Parses and serializes .properties files. Even though you can pretty
    much do this in your sleep, it's still useful for L10n tests.
    """

    def __init__(self, dtd):
        """
        Properties parsers can initialized based on a file path
        (provided as a string to the path), or directly (in memory as a
        StringIO object).
        """

        self.entities = {}
        self.items = []

        if isinstance(dtd, types.StringTypes):
            data = open(dtd).read()
        elif isinstance(dtd, StringIO):
            data = dtd.getvalue()
        elif isinstance(dtd, file):
            data = dtd.read()

        # Create a context!
        self.context = ContextGenerator(data)

        split_data = data.split('\n')
        line_buffer = None
        line_number = 0
        for line in split_data:

            # Increment the line number
            line_number += 1

            # Clean things up
            clean_line = line.strip()
            if not clean_line:
                continue
            if clean_line.startswith('#'):
                continue

            # It's a line that wraps
            if clean_line.count('=') == 0:
                if line_buffer:
                    line_buffer[-1] += clean_line
                else:
                    continue
            else:

                if line_buffer:
                    # This line terminates a wrapped line
                    self.entities[line_buffer[0].strip()] = \
                        line_buffer[1].strip()
                    self.items.append((line_buffer[0].strip(),
                                       line_buffer[1].strip(),
                                       line_number))

                line_buffer = clean_line.split('=', 1)

        # Handle any left-over wrapped line data
        if line_buffer:
            self.entities[line_buffer[0].strip()] = \
                line_buffer[1].strip()
            self.items.append((line_buffer[0].strip(),
                               line_buffer[1].strip(),
                               line_number))

    def __len__(self):
        return len(self.entities)

