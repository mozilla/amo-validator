import codecs
import simplejson as json
import os
import re
import subprocess
import tempfile
from cStringIO import StringIO

from validator.contextgenerator import ContextGenerator
import validator.unicodehelper as unicodehelper

JS_ESCAPE = re.compile("\\\\+[ux]", re.I)


def get_tree(code, err=None, filename=None, shell=None):
    "Retrieves the parse tree for a JS snippet"

    if not code or not shell:
        return None

    try:
        return _get_tree(code, shell)
    except JSReflectException as exc:
        str_exc = str(exc).strip("'\"")
        if ("SyntaxError" in str_exc or
            "ReferenceError" in str_exc):
            err.warning(("testcases_scripting",
                         "test_js_file",
                         "syntax_error"),
                         "JavaScript Compile-Time Error",
                         ["A compile-time error in the JavaScript halted "
                          "validation of that file.",
                          "Message: %s" % str_exc.split(":", 1)[-1].strip()],
                         filename=filename,
                         line=exc.line,
                         context=ContextGenerator(code))
        elif "InternalError: too much recursion" in str_exc:
            err.notice(("testcases_scripting",
                        "test_js_file",
                        "recursion_error"),
                       "JS too deeply nested for validation",
                       "A JS file was encountered that could not be valiated "
                       "due to limitations with Spidermonkey. It should be "
                       "manually inspected.",
                       filename=filename)
        else:
            err.error(("testcases_scripting",
                       "test_js_file",
                       "retrieving_tree"),
                      "JS reflection error prevented validation",
                      ["An error in the JavaScript file prevented it from "
                       "being properly read by the Spidermonkey JS engine.",
                       str(exc)],
                      filename=filename)


class JSReflectException(Exception):
    "An exception to indicate that tokenization has failed"

    def __init__(self, value):
        self.value = value
        self.line = None

    def __str__(self):
        return repr(self.value)

    def line_num(self, line_num):
        "Set the line number and return self for chaining"
        self.line = int(line_num)
        return self


def prepare_code(code):
    """Prepare code for tree generation."""

    code = unicodehelper.decode(code)
    # Acceptable unicode characters still need to be stripped. Just remove the
    # slash: a character is necessary to prevent bad identifier errors.
    return JS_ESCAPE.sub("u", code)


def _get_tree(code, shell):
    "Returns an AST tree of the JS passed in `code`."

    if not code:
        return None

    code = prepare_code(code)

    temp = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    temp.write(code.encode("utf_8"))
    temp.flush()

    data = """
    try{options("allow_xml");}catch(e){}
    try{
        print(JSON.stringify(Reflect.parse(read(%s))));
    } catch(e) {
        print(JSON.stringify({
            "error":true,
            "error_message":e.toString(),
            "line_number":e.lineNumber
        }));
    }""" % json.dumps(temp.name)

    try:
        cmd = [shell, "-e", data, "-U"]
        shell_obj = subprocess.Popen(cmd,
                                     shell=False,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)

        data, stderr = shell_obj.communicate()
        if stderr and not data:
            raise RuntimeError('Error calling %r: %s' % (cmd, stderr))

        # Closing the temp file will delete it.
    finally:
        try:
            temp.close()
            os.unlink(temp.name)
        except IOError:
            pass

    if not data:
        raise JSReflectException("Reflection failed")

    data = unicodehelper.decode(data)
    parsed = json.loads(data, strict=False)

    if "error" in parsed and parsed["error"]:
        if parsed["error_message"].startswith("ReferenceError: Reflect"):
            raise RuntimeError("Spidermonkey version too old; "
                               "1.8pre+ required; error='%s'; "
                               "spidermonkey='%s'" % (parsed["error_message"],
                                                      shell))
        else:
            raise JSReflectException(parsed["error_message"]).line_num(
                    parsed["line_number"])

    return parsed

