import json
from StringIO import StringIO

import validator.main
import validator.constants
import validator.testcases.targetapplication
from validator.errorbundler import ErrorBundle
from validator.constants import PACKAGE_ANY


def validate(path, format="json",
             approved_applications="validator/app_versions.json",
             determined=True,
             spidermonkey=None):
    "Perform validation in one easy step!"

    output = StringIO()
    
    # Load up the target applications
    apps = json.load(open(approved_applications))
    validator.testcases.targetapplication.APPROVED_APPLICATIONS = apps

    bundle = ErrorBundle(pipe=output, no_color=True, listed=True,
                         determined=determined)
    if spidermonkey is not None:
        bundle.save_resource("SPIDERMONKEY", spidermonkey)

    validator.main.prepare_package(bundle, path, PACKAGE_ANY)

    # Write the results to the pipe
    formats = {"json": lambda b:bundle.print_json()}
    if format in formats:
        formats[format](bundle)
    
    # Return the output of the validator
    return output.getvalue()

