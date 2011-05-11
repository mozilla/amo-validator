import validator.constants
import validator.decorator as decorator
from validator.constants import *

def versions_after(guid, version):
    """Returns all values after (and including) `version` for the app `guid`"""

    app_versions = validator.constants.APPROVED_APPLICATIONS
    app_key = None

    # Support for shorthand instead of full GUIDs.
    for app_guid, app_name in APPLICATIONS.items():
        if app_name == guid:
            guid = app_guid
            break

    for key in app_versions.keys():
        if app_versions[key]["guid"] == guid:
            app_key = key
            break

    if not app_key or version not in app_versions[app_key]["versions"]:
        raise Exception("Bad GUID or version provided for version range")

    version_pos = app_versions[app_key]["versions"].index(version)
    return app_versions[app_key]["versions"][version_pos:]


@decorator.register_test(tier=5,
                         versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                       versions_after("firefox", "4.2a1pre")})
def firefox_5_test(err, package, xpi):
    """Output a test message when Firefox 5 is supported."""
    err.notice(
        err_id=("testcases_compatibility",
                "firefox_5_test",
                "fx5_notice"),
        notice="Firefox 5 Compatibility Detected",
        description="Potential compatibility for FX5 was detected.",
        for_appversions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                             versions_after("firefox", "4.2a1pre")},
        compatibility_type="notice")


@decorator.register_test(tier=5,
                         versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                       versions_after("firefox", "4.2a1pre")})
def navigator_language(err, package, xpi):
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
            for_appversions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                 versions_after("firefox", "4.2a1pre")},
            compatibility_type="error")

