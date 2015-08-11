from StringIO import StringIO
import unicodehelper


INFINITY = float('inf')


class ContextGenerator:
    """The context generator creates a line-by-line mapping of all files that
    are validated. It will then use that to help produce useful bits of code
    for errors, warnings, and the like."""

    def __init__(self, data=None):
        if isinstance(data, StringIO):
            data = data.getvalue()

        self.data = data.split('\n')

    def get_context(self, line=1, column=0):
        'Returns a tuple containing the context for a line'

        line -= 1  # The line is one-based

        # If there is no data in the file, there can be no context.
        datalen = len(self.data)
        if datalen <= line:
            return None

        build = [self.data[line]]

        # Add surrounding lines if they're available. There must always be
        # three elements in the context.
        if line > 0:
            build.insert(0, self.data[line - 1])
        else:
            build.insert(0, None)

        if line < datalen - 1:
            build.append(self.data[line + 1])
        else:
            build.append(None)

        leading_counts = []

        # Count whitespace to determine how much needs to be stripped.
        lstrip_count = INFINITY
        for line in build:
            # Don't count empty/whitespace-only lines.
            if line is None or not line.strip():
                leading_counts.append(lstrip_count)
                continue

            # Isolate the leading whitespace.
            ws_count = len(line) - len(line.lstrip())
            leading_counts.append(ws_count)
            if ws_count < lstrip_count:
                lstrip_count = ws_count

        # If all of the lines were skipped over, it means everything was
        # whitespace.
        if lstrip_count == INFINITY:
            return ('', '', '')

        for lnum in range(3):
            # Skip edge lines.
            if not build[lnum]:
                continue

            line = build[lnum].strip()

            # Empty lines stay empty.
            if not line:
                build[lnum] = ''
                continue

            line = self._format_line(line, column=column, rel_line=lnum)
            line = '%s%s' % (' ' * (leading_counts[lnum] - lstrip_count), line)

            build[lnum] = line

        # Return the final output as a tuple.
        return tuple(build)

    def _format_line(self, data, column=0, rel_line=1):
        'Formats a line from the data to be the appropriate length'
        line_length = len(data)

        if line_length > 140:
            if rel_line == 0:
                # Trim from the beginning
                data = '... %s' % data[-140:]
            elif rel_line == 1:
                # Trim surrounding the error position
                if column < 70:
                    data = '%s ...' % data[:140]
                elif column > line_length - 70:
                    data = '... %s' % data[-140:]
                else:
                    data = '... %s ...' % data[column - 70:column + 70]

            elif rel_line == 2:
                # Trim from the end
                data = '%s ...' % data[:140]

        data = unicodehelper.decode(data)
        return data

    def get_line(self, position):
        'Returns the line number that the given string position is found on'

        datalen = len(self.data)
        count = len(self.data[0])
        line = 1
        while count < position:
            if line >= datalen:
                break
            count += len(self.data[line]) + 1
            line += 1

        return line

