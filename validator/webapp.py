import json
import re
import types
import urlparse

from unicodehelper import decode
from validator.specs.webapps import WebappSpec


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

    from validator.specs.webapps import WebappSpec
    ws = WebappSpec(webapp, err)
    ws.validate()

