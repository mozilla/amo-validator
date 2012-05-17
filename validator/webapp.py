import json
import re
import types
import urlparse

from validator.constants import *
from unicodehelper import decode


MAX_LENGTHS = {"name": 128,
               "description": 1024}
# TODO: `widget` is deprecated but we should eventually make it invalid.
VALID_KEYS = set(["name", "description", "launch_path", "icons", "developer",
                  "locales", "default_locale", "installs_allowed_from",
                  "version", "widget", "services", "experimental",
                  "screen_size", "required_features", "orientation",
                  "fullscreen"])
INVALID_LOCALE_KEYS = set(["locales", "default_locale",
                           "installs_allowed_from", ])
DEVELOPER_KEYS = set(["name", "url", ])
SCREEN_SIZE_KEYS = set(["min_width", "min_height"])
ORIENTATION_KEYS = set(["portrait", "landscape", "portrait-secondary",
                        "landscape-secondary"])


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
        valid = (path.startswith(("/", "http://", "https://"))
                 and not path.startswith("//"))

    return valid


def detect_webapp(err, package):
    """Detect, parse, and validate a webapp manifest."""

    # Parse the file.
    try:
        with open(package, mode="r") as f:
            data = f.read()
            u_data = decode(data)
            webapp = json.loads(u_data)
    except ValueError:
        return err.error(
            err_id=("webapp",
                    "detect_webapp",
                    "parse_error"),
            error="JSON Parse Error",
            description="The webapp extension could not be parsed due to a "
                        "syntax error in the JSON.")

    return test_webapp(err, webapp, VALID_KEYS)


def test_webapp(err, webapp, current_valid_keys, required=True):
    # Make sure that there is exactly one ShortName.
    if (("name" not in webapp or
         not isinstance(webapp["name"], types.StringTypes)) and required):
        err.error(
            err_id=("webapp", "detect", "name_missing"),
            error="Missing 'name' property",
            description="The 'name' value in the webapp manifest is a "
                        "required element that has not been found or is "
                        "invalid.")

    for key in webapp:
        if key not in current_valid_keys:
            err.error(
                err_id=("webapp", "detect", "invalid_key"),
                error="Unknown property found.",
                description=["An unknown property was found in the webapp "
                             "manifest.",
                             "Found property: %s" % key])
            continue

        key_length = len(webapp[key])
        if key in MAX_LENGTHS and MAX_LENGTHS[key] < len(webapp[key]):
            err.error(
                err_id=("webapp", "detect", "too_long"),
                error="Key value too long",
                description=["A key in the manifest has a value that is too "
                             "long.",
                             ("The max length of '%s' is %d. Your '%s' is %d "
                              "characters.") %
                                 (key, MAX_LENGTHS[key], key, key_length)])

        if key == "developer":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "dev_dict"),
                    error="'developer' property is not an object.",
                    description="The 'developer' property must be an object.")
                continue

            keys = set(webapp[key].keys())
            extra_keys = keys - DEVELOPER_KEYS
            if extra_keys:
                err.warning(
                    err_id=("webapp", "detect", "extra_dev"),
                    warning="Extra keys in 'developer'.",
                    description=["The 'developer' key contains extra keys "
                                 "that could not be identified.",
                                 "Extra keys: %s" %
                                     ", ".join(extra_keys)])
            if "name" not in keys and required:
                err.error(
                    err_id=("webapp", "detect", "absent_dev"),
                    error="Missing 'name' in 'developer'.",
                    description=["The 'developer' key is missing a name."])

            if ("url" in keys and
                not _test_url(webapp[key]["url"])):
                err.error(
                    err_id=("webapp", "detect", "bad_dev_url"),
                    error="Developer URL is not valid.",
                    description=["The developer URL key is not valid.",
                                 "Bad URL: %s" % webapp[key]["url"]])
        elif key == "icons":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "icons_not_dict"),
                    error="'icons' property not an object.",
                    description="The 'icons' property is not an object, "
                                "though it should be.")
                continue

            for size in webapp[key]:
                if not size.isdigit():
                    err.error(
                        err_id=("webapp", "detect", "size_not_num"),
                        error="Icon size is not a number.",
                        description=["Icon sizes (keys) must be natural "
                                     "numbers.",
                                     "Invalid size: %s" % size])
                if not test_path(webapp[key][size], can_be_data=True):
                    err.error(
                        err_id=("webapp", "detect", "invalid_icon"),
                        error="Icon path invalid",
                        description=["The path for an icon is invalid.",
                                     "Icon size: %s" % size,
                                     "Path: %s" % webapp[key][size]])
        elif key == "installs_allowed_from":
            if not isinstance(webapp[key], list):
                err.error(
                    err_id=("webapp", "detect", "bad_iaf_type"),
                    error="'installs_allowed_from' must be a list.",
                    description="The value of 'installs_allowed_from' in the "
                                "manifest must be an array of values.")
                continue

            for url in webapp[key]:
                if not _test_url(url, can_be_asterisk=True):
                    err.error(
                        err_id=("webapp", "detect", "bad_iaf_url"),
                        error="'installs_allowed_from' URL invalid.",
                        description=["A URL from 'installs_allowed_from' is "
                                     "invalid.",
                                     "Bad URL: %s" % url])

            # If none of the acceptable webapp installation URLs are present
            # and the webapp doesn't allow installs from "*" and the webapp is
            # headed for the marketplace, report an error.
            if (all(url not in webapp[key] for url in
                    DEFAULT_WEBAPP_MRKT_URLS) and
                "*" not in webapp[key] and err.get_resource("listed")):
                err.error(
                    err_id=("webapp", "detect", "iaf_no_amo"),
                    error=("App must allow installs from Marketplace "
                           "for inclusion."),
                    description="To be included on %s, a webapp needs to "
                                "include %s, or '*' (wildcard) as an element "
                                "in the 'installs_allowed_from' property." %
                                    (DEFAULT_WEBAPP_MRKT_URLS[0],
                                     ", ".join(DEFAULT_WEBAPP_MRKT_URLS)))

        elif key == "launch_path":
            if not isinstance(webapp[key], types.StringTypes):
                err.error(
                    err_id=("webapp", "detect", "launch_path_not_str"),
                    error="'launch_path' property not string.",
                    description="The 'launch_path' property of the manifest "
                                "must be a string.")
                continue

            if not test_path(webapp[key]):
                err.error(
                    err_id=("webapp", "detect", "launch_path"),
                    error="'launch_path' is not a valid path.",
                    description=["The 'launch_path' element is not a valid "
                                 "path.",
                                 "Bad path: %s" % webapp[key]])
        elif key == "locales":
            if "default_locale" not in webapp:
                err.error(
                    err_id=("webapp", "detect", "default_locale"),
                    error="No default locale set.",
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
            err.warning(
                err_id=("webapp", "detect", "widget_is_deprecated"),
                warning="'widget' property is deprecated.",
                description=["The 'widget' property is deprecated and is "
                             "no longer supported."])
        elif key == "screen_size":
            if not isinstance(webapp[key], dict):
                err.error(
                    err_id=("webapp", "detect", "screen_size_dict"),
                    error="'screen_size' property is not an object.",
                    description="The 'screen_size' property must be an "
                                "object.")
                continue

            keys = set(webapp[key].keys())
            extra_keys = keys - SCREEN_SIZE_KEYS
            if extra_keys:
                err.warning(
                    err_id=("webapp", "detect", "extra_screen_size"),
                    warning="Extra keys in 'screen_size'.",
                    description=["The 'screen_size' key contains extra keys "
                                 "that could not be identified.",
                                 "Extra keys: %s" % ", ".join(extra_keys)])

            for field, size in webapp[key].iteritems():
                if not size.isdigit():
                    err.error(
                        err_id=("webapp", "detect", "screen_size_not_num"),
                        error="Screen size '%s' is not a number." % field,
                        description=["Icon sizes (keys) must be natural "
                                     "numbers.",
                                     "Invalid size: %s" % size])

            if not any([s in keys for s in SCREEN_SIZE_KEYS]) and required:
                err.error(
                    err_id=("webapp", "detect", "absent_screen_size"),
                    error="Missing 'min_width' or 'min_height' in "
                          "'screen_size'.",
                    description=["The 'screen_size' key must contain at least "
                                 "one value: 'min_width' or 'min_height'"])
        elif key == "required_features":
             if not isinstance(webapp[key], list):
                 err.error(
                     err_id=("webapp", "detect", "required_features_list"),
                     error="'required_features' property is not a list.",
                     description="The values of 'required_features' must be "
                                 "an array of values.")
                 continue
        elif key == "orientation":
            if not isinstance(webapp[key], basestring):
                err.error(
                    err_id=("webapp", "detect", "orientation_string"),
                    error="'orientation' property is not a string.",
                    description="The value of 'orientation' must be a string.")
                continue
            if webapp[key] not in ORIENTATION_KEYS and required:
                err.error(
                    err_id=("webapp", "detect", "extra_orientation"),
                    error="Invalid value for 'orientation'.",
                    description=["The value for the 'orientation' key "
                                 "contains incorrect values. ",
                                 "Acceptable values: %s" %
                                 ", ".join(ORIENTATION_KEYS)])
        elif key == "fullscreen":
            if not isinstance(webapp[key], basestring):
                err.error(
                    err_id=("webapp", "detect", "fullscreen_string"),
                    error="'fullscreen' property is not a list.",
                    description="The value of 'fullscreen' must be a string.")
                continue
            if webapp[key] not in ("true", "false"):
                err.error(
                    err_id=("webapp", "detect", "fullscreen_boolean"),
                    error="'fullscreen' property is not a boolean.",
                    description="The value of 'fullscreen' must be a boolean.")
