import sys
import os

import zipfile
from StringIO import StringIO

import argparse
import validator.submain as submain
import validator.testcases.packagelayout
import validator.testcases.installrdf
import validator.testcases.library_blacklist
import validator.testcases.conduit
import validator.testcases.langpack
import validator.testcases.themes
import validator.testcases.content
import validator.testcases.targetapplication
import validator.testcases.l10ncompleteness
from validator.submain import *
from errorbundler import ErrorBundle
from validator.constants import *

def main():
    "Main function. Handles delegation to other functions."
    
    expectations = {"any":PACKAGE_ANY,
                    "extension":PACKAGE_EXTENSION,
                    "theme":PACKAGE_THEME,
                    "dictionary":PACKAGE_DICTIONARY,
                    "languagepack":PACKAGE_LANGPACK,
                    "search":PACKAGE_SEARCHPROV,
                    "multi":PACKAGE_MULTI}

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
    parser.add_argument("--file",
                        type=argparse.FileType("w"),
                        default=sys.stdout,
                        help="""Specifying a path will write the output
                        of the analysis to a file rather than to the
                        screen.""")
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

    args = parser.parse_args()

    error_bundle = ErrorBundle(args.file,
        not args.file == sys.stdout or args.boring)
    error_bundle.determined = args.determined

    # Emulates the "$status" variable in the original validation.php
    # test file. Equal to "$status == STATUS_LISTED".
    error_bundle.save_resource("listed", not args.selfhosted)

    # Parse out the expected add-on type and run the tests.
    expectation = expectations[args.type]
    submain.prepare_package(error_bundle, args.package, expectation)

    # Print the output of the tests based on the requested format.
    if args.output == "text":
        error_bundle.print_summary(args.verbose)
    elif args.output == "json":
        error_bundle.print_json()

    # Close the output stream.
    args.file.close()

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)

# Start up the testing and return the output.
if __name__ == '__main__':
    main()
