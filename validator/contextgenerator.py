import os
from StringIO import StringIO

# The context generator creates a line-by-line mapping of all files that are
# validated. It will then use that to help produce useful bits of code for
# errors, warnings, and the like.

class ContextGenerator:

    def __init__(self, data=None):
        if isinstance(data, StringIO):
            data = data.getvalue()
        
        self.data = data.split("\n")

    def get_context(self, line):
        "Returns a tuple containing the context for a line"
        
        line -= 1 # The line is one-based

        # If there is no data in the file, there can be no context.
        datalen = len(self.data)
        if datalen <= line:
            return None
        
        build = [self.data[line]]

        # Add surrounding lines if they're available.
        if line > 0:
            build.insert(0, self.data[line - 1])
        if line < datalen - 1:
            build.append(self.data[line + 1])

        for i in range(len(build)):
            # This erases all leading whitespace. Perhaps we should keep it?
            build[i] = build[i].strip()
            # Truncate each line to 140-ish characters
            if len(build[i]) >= 140:
                build[i] = "%s ..." % build[i][:140]

        # Return the final output as a tuple.
        return tuple(build)

    def get_line(self, position):
        "Returns the line that the given string position would be found on"

        count = len(self.data[0])
        line = 1
        while count < position:
            count += len(self.data[line])
            line += 1

        return line

