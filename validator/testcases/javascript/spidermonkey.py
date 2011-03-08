import json
import os
import re
import subprocess
import tempfile
from cStringIO import StringIO

from validator.constants import SPIDERMONKEY_INSTALLATION
from validator.contextgenerator import ContextGenerator
from validator.textfilter import *

JS_ESCAPE = re.compile("\\\\+[ux]", re.I)


def get_tree(code, err=None, filename=None, shell=None):
    "Retrieves the parse tree for a JS snippet"

    if not code:
        return None

    # Filter characters, convert to Unicode, etc.
    code = prepare_code(code, err, filename)

    try:
        tree = _get_tree(code,
                         shell if shell else SPIDERMONKEY_INSTALLATION)
        return tree
    except JSReflectException as exc:
        str_exc = str(exc).strip("'\"")
        if "SyntaxError" in str_exc:
            err.warning(("testcases_scripting",
                         "test_js_file",
                         "syntax_error"),
                         "JavaScript Syntax Error",
                         ["A syntax error in the JavaScript halted validation "
                          "of that file.",
                          "Message: %s" % str_exc[15:-1]],
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


def prepare_code(code, err, filename):
    "Prepares code for tree generation"
    # Acceptable unicode characters still need to be stripped. Just remove the
    # slash: a character is necessary to prevent bad identifier errors
    code = JS_ESCAPE.sub("u", code)

    encoding = None
    try:
        code = unicode(code) # Make sure we can get a Unicode representation
        code = strip_weird_chars(code, err=err, name=filename)
    except UnicodeDecodeError:
        # If it's not an easily decodeable encoding, detect it and decode that
        code = filter_ascii(code)

    return code

def strip_weird_chars(chardata, err=None, name=""):
    line_num = 1
    out_code = StringIO()
    has_warned_ctrlchar = False

    for line in chardata.split("\n"):

        charpos = 0
        for char in line:
            if is_standard_ascii(char):
                out_code.write(char)
            else:
                if not has_warned_ctrlchar and err is not None:
                    err.warning(("testcases_scripting",
                                 "_get_tree",
                                 "control_char_filter"),
                                "Invalid control character in JS file",
                                "An invalid character (ASCII 0-31, except CR "
                                "and LF) has been found in a JS file. These "
                                "are considered unsafe and should be removed.",
                                filename=name,
                                line=line_num,
                                column=charpos,
                                context=ContextGenerator(chardata))
                has_warned_ctrlchar = True

            charpos += 1

        out_code.write("\n")
        line_num += 1

    return out_code.getvalue()

def _get_tree(code, shell=SPIDERMONKEY_INSTALLATION):
    "Returns an AST tree of the JS passed in `code`."

    if not code:
        return None

    temp = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    temp.write(code)
    temp.flush()

    data = """try{
        print(JSON.stringify(Reflect.parse(read(%s))));
    } catch(e) {
        print(JSON.stringify({
            "error":true,
            "error_message":e.toString(),
            "line_number":e.lineNumber
        }));
    }""" % json.dumps(temp.name)

    try:
        cmd = [shell, "-e", data]
        try:
            shell_obj = subprocess.Popen(cmd,
                                   shell=False,
                       stderr=subprocess.PIPE,
                       stdout=subprocess.PIPE)
        except OSError:
            raise OSError("Spidermonkey shell could not be run.")

        data, stderr = shell_obj.communicate()
        if stderr: raise RuntimeError('Error calling %r: %s' % (cmd, stderr))

        # Closing the temp file will delete it.
    finally:
        try:
            temp.close()
            os.unlink(temp.name)
        except: pass

    if not data:
        raise JSReflectException("Reflection failed")

    try:
        data = unicode(data)
    except UnicodeDecodeError:
        data = unicode(filter_ascii(data))

    parsed = json.loads(data, strict=False)

    if "error" in parsed and parsed["error"]:
        if parsed["error_message"][:14] == "ReferenceError":
            raise RuntimeError("Spidermonkey version too old; "
                               "1.8pre+ required; error='%s'; "
                               "spidermonkey='%s'" % (parsed["error_message"],
                                                      shell))
        else:
            raise JSReflectException(parsed["error_message"]).line_num(
                    parsed["line_number"])

    return parsed

