import argparse
import json
import logging
import sys

from validator import constants
from validator.validate import validate


def main():
    'Main function. Handles delegation to other functions.'

    logging.basicConfig()

    type_choices = {'any': constants.PACKAGE_ANY,
                    'extension': constants.PACKAGE_EXTENSION,
                    'theme': constants.PACKAGE_THEME,
                    'dictionary': constants.PACKAGE_DICTIONARY,
                    'languagepack': constants.PACKAGE_LANGPACK,
                    'search': constants.PACKAGE_SEARCHPROV,
                    'multi': constants.PACKAGE_MULTI}

    # Parse the arguments that
    parser = argparse.ArgumentParser(
        description='Run tests on a Mozilla-type addon.')

    parser.add_argument('package',
                        help="The path of the package you're testing")
    parser.add_argument('-t',
                        '--type',
                        default='any',
                        choices=type_choices.keys(),
                        help="Type of addon you assume you're testing",
                        required=False)
    parser.add_argument('-o',
                        '--output',
                        default='text',
                        choices=('text', 'json'),
                        help='The output format that you expect',
                        required=False)
    parser.add_argument('-v',
                        '--verbose',
                        action='store_const',
                        const=True,
                        help="""If the output format supports it, makes
                        the analysis summary include extra info.""")
    parser.add_argument('--boring',
                        action='store_const',
                        const=True,
                        help="""Activating this flag will remove color
                        support from the terminal.""")
    parser.add_argument('--determined',
                        action='store_const',
                        const=True,
                        help="""This flag will continue running tests in
                        successive tests even if a lower tier fails.""")
    parser.add_argument('--selfhosted',
                        action='store_const',
                        const=True,
                        help="""Indicates that the addon will not be
                        hosted on addons.mozilla.org. This allows the
                        <em:updateURL> element to be set.""")
    parser.add_argument('--approved_applications',
                        help="""A JSON file containing acceptable applications
                        and their versions""",
                        required=False)
    parser.add_argument('--target-maxversion',
                        help="""JSON string to override the package's
                        targetapp_maxVersion for validation. The JSON object
                        should be a dict of versions keyed by application
                        GUID. For example, setting a package's max Firefox
                        version to 5.*:
                        {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": "5.*"}
                        """)
    parser.add_argument('--target-minversion',
                        help="""JSON string to override the package's
                        targetapp_minVersion for validation. The JSON object
                        should be a dict of versions keyed by application
                        GUID. For example, setting a package's min Firefox
                        version to 5.*:
                        {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": "5.*"}
                        """)
    parser.add_argument('--for-appversions',
                        help="""JSON string to run validation tests for
                        compatibility with a specific app/version. The JSON
                        object should be a dict of version lists keyed by
                        application GUID. For example, running Firefox 6.*
                        compatibility tests:
                        {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": ["6.*"]}
                        """)
    parser.add_argument('--timeout',
                        help='The amount of time before validation is '
                             'terminated with a timeout exception.',
                        default='60')

    args = parser.parse_args()

    # We want to make sure that the output is expected. Parse out the expected
    # type for the add-on and pass it in for validation.
    if args.type not in type_choices:
        # Fail if the user provided invalid input.
        print 'Given expectation (%s) not valid. See --help for details' % \
                args.type
        sys.exit(1)

    overrides = {}
    if args.target_minversion:
        overrides['targetapp_minVersion'] = json.loads(args.target_minversion)
    if args.target_maxversion:
        overrides['targetapp_maxVersion'] = json.loads(args.target_maxversion)

    for_appversions = None
    if args.for_appversions:
        for_appversions = json.loads(args.for_appversions)

    try:
        timeout = int(args.timeout)
    except ValueError:
        print 'Invalid timeout. Integer expected.'
        sys.exit(1)

    expectation = type_choices[args.type]
    error_bundle = validate(args.package,
                            format=None,
                            approved_applications=args.approved_applications,
                            determined=args.determined,
                            listed=not args.selfhosted,
                            overrides=overrides,
                            for_appversions=for_appversions,
                            expectation=expectation,
                            timeout=timeout)

    # Print the output of the tests based on the requested format.
    if args.output == 'text':
        print error_bundle.print_summary(verbose=args.verbose,
                                         no_color=args.boring).encode('utf-8')
    elif args.output == 'json':
        sys.stdout.write(error_bundle.render_json())

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)

# Start up the testing and return the output.
if __name__ == '__main__':
    main()
