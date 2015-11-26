import simplejson as json

from spidermonkey import Spidermonkey

from validator import unicodehelper
from validator.contextgenerator import ContextGenerator
from validator.decorator import register_cleanup


def get_tree(code, err=None, filename=None, shell=None):
    """Retrieve the parse tree for a JS snippet."""

    try:
        return JSShell.get_shell().get_tree(code)
    except JSReflectException as exc:
        str_exc = str(exc)
        if 'SyntaxError' in str_exc or 'ReferenceError' in str_exc:
            err.warning(('testcases_scripting', 'test_js_file',
                         'syntax_error'),
                        'JavaScript Compile-Time Error',
                        ['A compile-time error in the JavaScript halted '
                         'validation of that file.',
                         'Message: %s' % str_exc.split(':', 1)[-1].strip()],
                        filename=filename,
                        line=exc.line,
                        context=ContextGenerator(code))
        elif 'InternalError: too much recursion' in str_exc:
            err.notice(('testcases_scripting', 'test_js_file',
                        'recursion_error'),
                       'JS too deeply nested for validation',
                       'A JS file was encountered that could not be valiated '
                       'due to limitations with Spidermonkey. It should be '
                       'manually inspected.',
                       filename=filename)
        else:
            err.error(('testcases_scripting', 'test_js_file',
                       'retrieving_tree'),
                      'JS reflection error prevented validation',
                      ['An error in the JavaScript file prevented it from '
                       'being properly read by the Spidermonkey JS engine.',
                       str(exc)],
                      filename=filename)


@register_cleanup
class JSShell(Spidermonkey):
    instance = None

    SCRIPT = """
        function output(object) {
            print(JSON.stringify(object));
        }
        var stdin;
        while ((stdin = readline())) {
            try{
                stdin = JSON.parse(stdin);
                output(Reflect.parse(stdin));
            } catch(e) {
                output({
                    "error": true,
                    "error_message": e.toString(),
                    "line_number": e.lineNumber
                });
            }
        }
    """

    def __init__(self):
        # Use "version(180)" so we don't use the latest version (185 at the
        # time of this writing:
        # https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/JSAPI_reference/JSVersion)  # noqa
        # which deprecates generators with 'function' (see
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/Legacy_generator_function)  # noqa
        super(JSShell, self).__init__(code=['version(180)', self.SCRIPT])

    def __del__(self):
        if self.returncode is None:
            self.terminate()
        super(Spidermonkey, self).__del__()

    @classmethod
    def get_shell(cls):
        """Get a running JSShell instance, or create a new one if one does not
        already exist."""

        if not cls.instance:
            cls.instance = cls()

        return cls.instance

    @classmethod
    def cleanup(cls):
        """Clear our saved instance, and terminate its Spidermonkey process,
        if there are no further references to it."""
        cls.instance = None

    def get_tree(self, code):
        if isinstance(code, str):
            code = unicodehelper.decode(code)

        try:
            self.stdin.write(json.dumps(code))
            self.stdin.write('\n')

            output = json.loads(self.stdout.readline(), strict=False)
        except Exception:
            # If this instance is the cached instance, clear it.
            if self == self.__class__.instance:
                self.__class__.instance = None
            raise

        if output.get('error'):
            raise JSReflectException(output['error_message'],
                                     output['line_number'])

        return output


class JSReflectException(Exception):
    'An exception to indicate that tokenization has failed'

    def __init__(self, value, line=None):
        self.value = value
        self.line = line

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '<JSReflectException (line {0}) {1!r}>'.format(
            self.line, self.value)
