import argparse
import json
import os
import sys
import zipfile
from StringIO import StringIO

from validator.validate import validate
from constants import *


def main():
    "Main function. Handles delegation to other functions."

    expectations = {"any": PACKAGE_ANY,
                    "extension": PACKAGE_EXTENSION,
                    "theme": PACKAGE_THEME,
                    "dictionary": PACKAGE_DICTIONARY,
                    "languagepack": PACKAGE_LANGPACK,
                    "search": PACKAGE_SEARCHPROV,
                    "multi": PACKAGE_MULTI}

    # Parse the arguments that
    parser = argparse.ArgumentParser(
        description="Run tests on a Mozilla-type addon.")

    parser.add_argument("package",
                        help="The path of the package you're testing")
    parser.add_argument("-t",
                        "--type",
                        default="any",
                        choices=expectations.keys(),
                        help="Type of addon you assume you're testing",
                        required=False)
    parser.add_argument("-o",
                        "--output",
                        default="text",
                        choices=("text", "json"),
                        help="The output format that you expect",
                        required=False)
    parser.add_argument("-v",
                        "--verbose",
                        action="store_const",
                        const=True,
                        help="""If the output format supports it, makes
                        the analysis summary include extra info.""")
    parser.add_argument("--boring",
                        action="store_const",
                        const=True,
                        help="""Activating this flag will remove color
                        support from the terminal.""")
    parser.add_argument("--determined",
                        action="store_const",
                        const=True,
                        help="""This flag will continue running tests in
                        successive tests even if a lower tier fails.""")
    parser.add_argument("--selfhosted",
                        action="store_const",
                        const=True,
                        help="""Indicates that the addon will not be
                        hosted on addons.mozilla.org. This allows the
                        <em:updateURL> element to be set.""")
    parser.add_argument("--approved_applications",
                        default="validator/app_versions.json",
                        help="""A JSON file containing acceptable applications
                        and their versions""")

    args = parser.parse_args()

    # We want to make sure that the output is expected. Parse out the expected
    # type for the add-on and pass it in for validation.
    if args.type not in expectations:
        # Fail if the user provided invalid input.
        print "Given expectation (%s) not valid. See --help for details" % \
                args.type
        sys.exit(1)

    expectation = expectations[args.type]
    error_bundle = validate(args.package,
                            format=None,
                            approved_applications=args.approved_applications,
                            determined=args.determined,
                            listed=not args.selfhosted)

    # Print the output of the tests based on the requested format.
    if args.output == "text":
        print error_bundle.print_summary(verbose=args.verbose,
                                         no_color=args.boring)
    elif args.output == "json":
        sys.stdout.write(error_bundle.render_json())

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)

# Start up the testing and return the output.
if __name__ == '__main__':
    main()
