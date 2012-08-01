import json
import re
import types
import urlparse

from unicodehelper import decode
from validator.specs.webapps import WebappSpec


def detect_webapp(err, package):
    """Detect, parse, and validate a webapp manifest."""

    # Parse the file.
    with open(package, mode="r") as f:
        detect_webapp_string(err, f.read())


def detect_webapp_string(err, data):
    """
    Parse and validate a webapp based on the string version of the provided
    manifest.
    """
    try:
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
    else:
        detect_webapp_raw(err, webapp)


def detect_webapp_raw(err, webapp):
    """
    Parse and validate a webapp based on the dict version of the manifest.
    """

    from validator.specs.webapps import WebappSpec
    ws = WebappSpec(webapp, err)
    ws.validate()

    # This magic number brought to you by @cvan (see bug 770755)
    if "name" in webapp and len(webapp["name"]) > 9:
        err.warning(
                err_id=("webapp", "b2g", "name_truncated"),
                warning="App name may be truncated on Firefox OS devices.",
                description="Your app's name is long enough to possibly be "
                            "truncated on Firefox OS devices. Consider using "
                            "a shorter name for your app.")
