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
        
        datalen = len(self.data)
        if datalen <= line:
            return None
        
        output = [None, self.data[line], None]
        if line > 0:
            output[0] = self.data[line - 1]
        if line < datalen - 1:
            output[2] = self.data[line + 1]

        for i in range(3):
            if output[i] is not None and len(output[i]) >= 140:
                output[i] = "%s ..." % output[i][:140]

        return tuple(output)

    def get_line(self, position):
        "Returns the line that the given string position would be found on"

        count = len(self.data[0])
        line = 1
        while count < position:
            count += len(self.data[line])
            line += 1

        return line

