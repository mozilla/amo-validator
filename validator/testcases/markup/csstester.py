import re
import cssutils

from validator.constants import PACKAGE_THEME
from validator.contextgenerator import ContextGenerator
from validator.unicodehelper import NON_ASCII_FILTER


BAD_URL_PAT = ("url\(['\"]?(?!(chrome:|resource:))(\/\/|(ht|f)tps?:\/\/|data:)"
               ".*['\"]?\)")
BAD_URL = re.compile(BAD_URL_PAT, re.I)
REM_URL = re.compile("url\(['\"]?(\/\/|ht|f)tps?:\/\/.*['\"]?\)", re.I)

SKIP_TYPES = ('S', 'COMMENT')

DOWNLOADS_INDICATOR_BUG = 845408


def test_css_file(err, filename, data, line_start=1):
    'Parse and test a whole CSS file.'

    tokenizer = cssutils.tokenize2.Tokenizer()
    context = ContextGenerator(data)

    if data:
        # Remove any characters which aren't printable, 7-bit ASCII.
        data = NON_ASCII_FILTER.sub('', data)

    token_generator = tokenizer.tokenize(data)

    _run_css_tests(err,
                   tokens=token_generator,
                   filename=filename,
                   line_start=line_start - 1,
                   context=context)


def test_css_snippet(err, filename, data, line):
    'Parse and test a CSS nugget.'

    # Re-package to make it CSS-complete. Note the whitespace to prevent
    # the extra code from showing in the context output.
    data = '#foo{\n\n%s\n\n}' % data

    test_css_file(err, filename, data, line)


def _run_css_tests(err, tokens, filename, line_start=0, context=None):
    """Processes a CSS file to test it for things that could cause it
    to be harmful to the browser."""

    last_descriptor = None

    identity_box_mods = []
    unicode_errors = []
    downloads_indicator_selectors = []

    token_history = []

    while True:

        try:
            tok_type, value, line, position = tokens.next()
        except UnicodeDecodeError:
            unicode_errors.append(str(line + line_start))
            continue
        except StopIteration:
            break

        if tok_type in SKIP_TYPES:
            continue

        token_history.append((tok_type, value))

        # Save the last descriptor for reference.
        if tok_type in ('IDENT', 'FUNCTION'):
            if tok_type == 'IDENT':
                last_descriptor = value.lower()

        elif tok_type == 'URI':

            # If we hit a URI after -moz-binding, we may have a
            # potential security issue.
            if last_descriptor == '-moz-binding' and BAD_URL.match(value):
                # We need to make sure the URI is not remote.
                err.warning(
                    err_id=('css', '_run_css_tests', '-moz-binding_external'),
                    warning='Illegal reference to external scripts',
                    description='`-moz-binding` may not reference external '
                                'scripts in CSS. This is considered to be a '
                                'security issue. The script file must be '
                                'placed in the /content/ directory of the '
                                'package.',
                    filename=filename,
                    line=line + line_start,
                    context=context.get_context(line))
            elif (err.detected_type == PACKAGE_THEME and
                  REM_URL.match(value) and
                  token_history[-2][0] != 'NAMESPACE_SYM'):
                # If we're a theme and the URL is remote and the last token
                # wasn't a CSS namespace symbol, raise a warning.
                err.warning(
                    err_id=('css', '_run_css_tests', 'remote_url'),
                    warning='Themes may not reference remote resources',
                    description='Themes may not reference resources that are '
                                'stored on remote servers. All resources must '
                                'be stored locally within the theme.',
                    filename=filename,
                    line=line + line_start,
                    context=context.get_context(line))

        elif tok_type == 'HASH':
            # Search for interference with the identity box.
            if value == '#identity-box':
                identity_box_mods.append(str(line + line_start))
            elif value == '#downloads-indicator':
                downloads_indicator_selectors.append(str(line + line_start))

    if identity_box_mods and err.detected_type != PACKAGE_THEME:
        err.warning(('testcases_markup_csstester', '_run_css_tests',
                     'identity_box'),
                    'Modification to identity box.',
                    ['The identity box (#identity-box) is a sensitive piece '
                     'of the interface and should not be modified.',
                     'Lines: %s' % ', '.join(identity_box_mods)],
                    filename)

    if unicode_errors:
        err.info(('testcases_markup_csstester',
                  'test_css_file',
                  'unicode_decode'),
                 'Unicode decode error.',
                 ['While decoding a CSS file, an unknown character was '
                  'encountered, causing some problems.',
                  'Lines: %s' % ', '.join(unicode_errors)],
                 filename)
