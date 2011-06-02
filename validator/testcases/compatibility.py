import validator.constants
import validator.decorator as decorator
from validator.decorator import versions_after
from validator.constants import *

FX4_VERSIONS = ["3.7a1pre", "3.7a1", "3.7a2pre", "3.7a2", "3.7a3pre", "3.7a3",
                "3.7a4pre", "3.7a4", "3.7a5pre", "3.7a5", "3.7a6pre", "4.0b1",
                "4.0b2pre", "4.0b2", "4.0b3pre", "4.0b3", "4.0b4pre", "4.0b4",
                "4.0b5pre", "4.0b5", "4.0b6pre", "4.0b6", "4.0b7pre", "4.0b7",
                "4.0b8pre", "4.0b8", "4.0b9pre", "4.0b9", "4.0b10pre",
                "4.0b10", "4.0b11pre", "4.0b11", "4.0b12pre", "4.0b12", "4.0",
                "4.0.*"]

@decorator.register_test(tier=5,
                         versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                       FX4_VERSIONS})
def navigator_language(err, xpi):
    """Any use of `navigator.language` should be flagged."""

    compat_references = err.get_resource("compat_references")
    if (not compat_references or
        "navigator_language" not in compat_references):
        return

    for filename, line, context in compat_references["navigator_language"]:
        err.notice(
            err_id=("testcases_compatibility",
                    "navigator_language"),
            notice="navigator.language may not behave as expected",
            description="JavaScript code was found that references "
                        "navigator.language, which will no longer indicate "
                        "the language of Firefox's UI. To maintain existing "
                        "functionality, general.useragent.locale should be "
                        "used in place of `navigator.language`.",
            filename=filename,
            line=line,
            context=context,
            compatibility_type="error")

