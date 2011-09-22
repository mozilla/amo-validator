import json
import re
import types
import urlparse

from validator.constants import *


MAX_LENGTHS = {"name": 128,
               "description": 1024}
VALID_KEYS = set(["name", "description", "launch_path", "icons", "developer",
                  "locales", "default_locale", "installs_allowed_from",
                  "version", "widget", "services", "experimental"])
INVALID_LOCALE_KEYS = set(["locales", "default_locale",
                           "installs_allowed_from", ])
DEVELOPER_KEYS = set(["name", "url", ])
WIDGET_KEYS = set(["height", "width", "path", ])


def _test_url(url, can_be_asterisk=False):
    """Test a URL to make sure it's usable within a webapp."""

    if can_be_asterisk and url == "*":
        return True

    try:
        # Parse the URL and test to make sure mandatory components are present.
        parsed_url = urlparse.urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False

        # Make sure the URL is using HTTP[S]
        if parsed_url.scheme.lower() not in ("http", "https", ):
            return False

    except ValueError:
        return False

    return True


def test_path(path, can_be_data=False):
    valid = False
    if can_be_data:
        valid = path.startswith("data:")
    if not valid:
        valid = path.startswith("/") and not path.startswith("//")

    return valid


def detect_webapp(err, package):
    """Detect, parse, and validate a webapp manifest."""

    # Parse the file.
    try:
        with open(package, mode="r") as f:
            webapp = json.load(f)
    except:
        return err.error(
            err_id=("webapp",
                    "detect_webapp",
                    "parse_error"),
            error="Webapp: JSON Parse Error",
            description="The webapp extension could not be parsed due to a "
                        "syntax error in the JSON.")

    return test_webapp(err, webapp, VALID_KEYS)


def test_webapp(err, webapp, current_valid_keys, required=True):
    # Make sure that there is exactly one ShortName.
    if (("name" not in webapp or
         not isinstance(webapp["name"], types.StringTypes)) and required):
        err.error(
            err_id=("webapp", "detect", "name_missing"),
            error="Webapp: Missing 'name' property",
            description="The 'name' value in the webapp manifest is a "
                        "required element that has not been found or is "
                        "invalid.")

    # If the add-on is listed, make sure we test for installs_allowed_from.
    if (err.get_resource("listed") and required and
        "installs_allowed_from" not in webapp):
        err.error(
            err_id=("webapp", "detect", "iaf_missing_listed"),
            error="Webapp: Missing 'installs_allowed_from' property",
            description="In order to submit a webapp to %s, "
                        "'installs_allowed_from' must exist and must contain "
                        "%s." % (WEBAPP_AMO_URL, WEBAPP_AMO_URL))

    for key in webapp:
        if key not in current_valid_keys:
            err.error(
                err_id=("webapp", "detect", "invalid_key"),
                error="Webapp: Unknown property found.",
                description=["An unknown property was found in the webapp "
                             "manifest.",
                             "Found property: %s" % key])
            continue

        key_length = len(webapp[key])
        if key in MAX_LENGTHS and MAX_LENGTHS[key] < len(webapp[key]):
            err.error(
                err_id=("webapp", "detect", "too_long"),
                error="Webapp: key value too long",
                description=["A key in the manifest has a value that is too "
                             "long.",
                             ("The max length of '%s' is %d. Your '%s' is %d "
                              "characters.") %
                                 (key, MAX_LENGTHS[key], key, key_length)])

        if key == "developer":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "dev_dict"),
                    error="Webapp: 'developer' property is not an object.",
                    description="The 'developer' property must be an object.")
                continue

            keys = set(webapp[key].keys())
            absent_keys = DEVELOPER_KEYS - keys
            extra_keys = keys - DEVELOPER_KEYS
            if extra_keys:
                err.warning(
                    err_id=("webapp", "detect", "extra_dev"),
                    warning="Webapp: Extra keys in 'developer'.",
                    description=["The 'developer' key contains extra keys "
                                 "that could not be identified.",
                                 "Extra keys: %s" %
                                     ", ".join(extra_keys)])
            if absent_keys and required:
                err.error(
                    err_id=("webapp", "detect", "absent_dev"),
                    error="Webapp: Missing keys in 'developer'.",
                    description=["The 'developer' key is missing certain "
                                 "children.",
                                 "Missing keys: %s" %
                                     ", ".join(absent_keys)])

            if ("url" in keys and
                not _test_url(webapp[key]["url"])):
                err.error(
                    err_id=("webapp", "detect", "bad_dev_url"),
                    error="Webapp: Developer URL is not valid.",
                    description=["The developer URL key is not valid.",
                                 "Bad URL: %s" % webapp[key]["url"]])
        elif key == "icons":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "icons_not_list"),
                    error="Webapp: 'icons' property not an object.",
                    description="The 'icons' property is not an object, "
                                "though it should be.")
                continue

            for size in webapp[key]:
                if not size.isdigit():
                    err.error(
                        err_id=("webapp", "detect", "size_not_num"),
                        error="Webapp: Icon size not number.",
                        description=["Icon sizes (keys) must be natural "
                                     "numbers.",
                                     "Invalid size: %s" % size])
                if not test_path(webapp[key][size], can_be_data=True):
                    err.error(
                        err_id=("webapp", "detect", "invalid_icon"),
                        error="Webapp: Icon path invalid",
                        description=["The path for an icon is invalid.",
                                     "Icon size: %s" % size,
                                     "Path: %s" % webapp[key][size]])
        elif key == "installs_allowed_from":
            if not isinstance(webapp[key], list):
                err.error(
                    err_id=("webapp", "detect", "bad_iaf_type"),
                    error="Webapp: 'installs_allowed_from' must be a list",
                    description="The value of 'installs_allowed_from' in the "
                                "manifest must be an array of values.")
                continue

            for url in webapp[key]:
                if not _test_url(url, can_be_asterisk=True):
                    err.error(
                        err_id=("webapp", "detect", "bad_iaf_url"),
                        error="Webapp: 'installs_allowed_from'' URL invalid.",
                        description=["A URL from 'installs_allowed_from' is "
                                     "invalid.",
                                     "Bad URL: %s" % url])

            if (WEBAPP_AMO_URL not in webapp[key] and
                "*" not in webapp[key] and
                err.get_resource("listed")):
                err.error(
                    err_id=("webapp", "detect", "iaf_no_amo"),
                    error="Webapp: Webapps must list AMO for inclusion.",
                    description="To be included on %s, a webapp needs to "
                                "include %s as an element in the "
                                "'installs_allowed_from' property." %
                                    (WEBAPP_AMO_URL, WEBAPP_AMO_URL))

        elif key == "launch_path":
            if not isinstance(webapp[key], types.StringTypes):
                err.error(
                    err_id=("webapp", "detect", "launch_path_not_str"),
                    error="Webapp: 'launch_path' property not string.",
                    description="The 'launch_path' property of the manifest "
                                "must be a string.")
                continue

            if not test_path(webapp[key]):
                err.error(
                    err_id=("webapp", "detect", "launch_path"),
                    error="Webapp: 'launch_path' not a valid path",
                    description=["The 'launch_path' element is not a valid "
                                 "path.",
                                 "Bad path: %s" % webapp[key]])
        elif key == "locales":
            if "default_locale" not in webapp:
                err.error(
                    err_id=("webapp", "detect", "default_locale"),
                    error="Webapp: No default locale set",
                    description="When locales are available, 'default_locale' "
                                "must also be present.")

            for locale in webapp[key]:
                for locale_key in webapp[key][locale]:
                    valid_keys = set(VALID_KEYS) - set(INVALID_LOCALE_KEYS)
                    test_webapp(
                            err, webapp[key][locale],
                            current_valid_keys=valid_keys,
                            required=False)
        elif key == "widget":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "widget_is_dict"),
                    error="Webapp: 'widget' property is not an object.",
                    description="The 'widget' property must be an object.")
                continue

            for widget_key in webapp[key]:
                if widget_key not in WIDGET_KEYS:
                    err.error(
                        err_id=("webapp", "detect", "widget_keys"),
                        error="Webapp: Unknown property found in 'widget'.",
                        description=["An unknown key was found in the widget "
                                     "property.",
                                     "Property: %s" % widget_key])
                elif (widget_key == "path" and
                      not test_path(webapp[key]["path"])):
                    err.error(
                        err_id=("webapp", "detect", "widget_path"),
                        error="Webapp: Widget 'path' invalid.",
                        description=["The specified widget path key is "
                                     "invalid.",
                                     "Invalid path: %s" % webapp[key]["path"]])
                elif widget_key in ("height", "width", ):
                    if not (10 <= int(webapp[key][widget_key]) <= 1000):
                        err.error(
                            err_id=("webapp", "detect", "widget_size"),
                            error="Webapp: Widget size invalid.",
                            description="The 'height' or 'width' of the "
                                        "webapp's widget is invalid.")

            for widget_key in WIDGET_KEYS:
                if widget_key not in webapp[key]:
                    err.error(
                        err_id=("webapp", "detect", "widget_mand_keys"),
                        error="Webapp: Required widget elements missing",
                        description=["Keys that belong in the 'widget' key "
                                     "are missing.",
                                     "Key: %s" % widget_key])

