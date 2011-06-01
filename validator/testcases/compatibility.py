import validator.constants
import validator.decorator as decorator
from validator.decorator import versions_after
from validator.constants import *


@decorator.register_test(tier=5,
                         versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                       versions_after("firefox", "4.2a1pre")})
def navigator_language(err, xpi):
    """Any use of `navigator.language` should be flagged."""

    compat_references = err.get_resource("compat_references")
    if (not compat_references or
        "navigator_language" not in compat_references):
        return

    for filename, line, context in compat_references["navigator_language"]:
        err.warning(
            err_id=("testcases_compatibility",
                    "navigator_language"),
            warning="navigator.language may not behave as expected",
            description="JavaScript code was found that references "
                        "navigator.language, which will no longer indicate "
                        "the language of Firefox's UI. To maintain existing "
                        "functionality, general.useragent.locale should be "
                        "used in place of `navigator.language`.",
            filename=filename,
            line=line,
            context=context,
            compatibility_type="error")

