from cStringIO import StringIO

import validator.main
from validator.errorbundler import ErrorBundle
from validator.constants import PACKAGE_ANY


def validate(path, format="json"):
    "Perform validation in one easy step!"

    output = StringIO()

    bundle = ErrorBundle(pipe=output, no_color=True)
    bundle.determined = True # Run all tests, even if one tier fails
    bundle.save_resource("listed", True) # Add-on is headed for AMO
    
    validator.main.prepare_package(bundle, path, PACKAGE_ANY)

    # Write the results to the pipe
    formats = {"json": lambda b:bundle.print_json()}
    if format in formats:
        formats[format](bundle)
    
    # Return the output of the validator
    return output.getvalue()

