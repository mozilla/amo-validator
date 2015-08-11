import re
try:
    import curses
except ImportError:
    curses = None
import os
import sys

from StringIO import StringIO

COLORS = ('BLUE', 'RED', 'GREEN', 'YELLOW', 'WHITE', 'BLACK')


class OutputHandler:
    """A handler that hooks up with the error bundler to colorize the
    output of the application for *nix-based terminals."""

    def __init__(self, buffer=sys.stdout, no_color=False):
        if not curses:
            no_color = True
        if not no_color:
            no_color = isinstance(sys.stdout, StringIO) or \
                       not sys.stdout.isatty()

        self.no_color = no_color

        # Don't bother initiating color if there's no color.
        if not no_color:

            # Get curses all ready to write some stuff to the screen.
            curses.setupterm()

            # Initialize a store for the colors and pre-populate it
            # with the un-color color.
            self.colors = {'NORMAL': curses.tigetstr('sgr0') or ''}

            # Determines capabilities of the terminal.
            fgColorSeq = curses.tigetstr('setaf') or \
                curses.tigetstr('setf') or ''

            # Go through each color and figure out what the sequences
            # are for each, then store the sequences in the store we
            # made above.
            for color in COLORS:
                colorIndex = getattr(curses, 'COLOR_%s' % color)
                self.colors[color] = curses.tparm(fgColorSeq,
                                                  colorIndex)

        self.buffer = buffer

    def colorize_text(self, text):
        """Adds escape sequences to colorize text and make it
        beautiful. To colorize text, prefix the text you want to color
        with the color (capitalized) wrapped in double angle brackets
        (i.e.: <<GREEN>>). End your string with <<NORMAL>>. If you
        don't, it will be done for you (assuming you used a color code
        in your string."""

        # Take note of where the escape sequences are.
        rnormal = text.rfind('<<NORMAL')
        rany = text.rfind('<<')

        # Put in the escape sequences.
        for color, code in self.colors.items():
            text = text.replace('<<%s>>' % color, code)

        # Make sure that the last sequence is a NORMAL sequence.
        if rany > -1 and rnormal < rany:
            text += self.colors['NORMAL']

        return text

    def write(self, text):
        'Uses curses to print in the fanciest way possible.'

        # Add color to the terminal.
        if not self.no_color:
            text = self.colorize_text(text)
        else:
            pattern = re.compile('\<\<[A-Z]*?\>\>')
            text = pattern.sub('', text)

        text += '\n'

        self.buffer.write(text)

        return self

