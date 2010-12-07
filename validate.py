import json
from StringIO import StringIO

import validator.main
import validator.testcases.targetapplication
from validator.errorbundler import ErrorBundle
from validator.constants import PACKAGE_ANY


def validate(path, format="json", approved_applications="", determined=True):
    "Perform validation in one easy step!"

    output = StringIO()
    
    # Load up the target applications
    validator.testcases.targetapplication.APPROVED_APPLICATIONS = \
            json.loads(open(approved_applications if
                approved_applications else
                "validator/app_versions.json").read())

    bundle = ErrorBundle(pipe=output, no_color=True, listed=True,
                         determined=determined)
    validator.main.prepare_package(bundle, path, PACKAGE_ANY)

    # Write the results to the pipe
    formats = {"json": lambda b:bundle.print_json()}
    if format in formats:
        formats[format](bundle)
    
    # Return the output of the validator
    return output.getvalue()

