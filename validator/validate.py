import json
import os
import types

from . import constants
from .constants import PACKAGE_ANY
from .errorbundler import ErrorBundle
# This is necessary. Do not remove it unless you know exactly what
# you are doing.
import loader  # noqa
import submain


def validate(path, format="json",
             approved_applications=None,
             library_metadata=None,
             determined=True,
             spidermonkey=False,
             listed=True,
             expectation=PACKAGE_ANY,
             for_appversions=None,
             overrides=None,
             timeout=-1,
             compat_test=False,
             **kw):
    """
    Perform validation in one easy step!

    `path`:
        *Required*
        A file system path to the package to be validated.
    `format`:
        The format to return the results in. Defaults to "json". Currently, any
        other format will simply return the error bundle.
    `approved_applications`:
        List of approved application versions, provided either as a path
        to a JSON file, or as an appropriate Python data structure.
    `library_metadata`:
        Metadata for approved libraries and frameworks, provided either as a
        path to a JSON file, or as an appropriate Python data structure.
    `determined`:
        If set to `False`, validation will halt at the end of the first tier
        that raises errors.
    `spidermonkey`:
        Path to the local spidermonkey installation. Defaults to `False`, which
        uses the validator's built-in detection of Spidermonkey. Specifying
        `None` will disable JavaScript tests. Any other value is treated as the
        path.
    `listed`:
        Whether the app is headed for the app marketplace or AMO. Defaults to
        `True`.
    `expectation`:
        The type of package that should be expected. Must be a symbolic
        constant from validator.constants (i.e.:
        validator.constants.PACKAGE_*). Defaults to PACKAGE_ANY.
    `for_appversions`:
        A dict of app GUIDs referencing lists of versions. Determines which
        version-dependant tests should be run.
    `timeout`:
        Number of seconds before aborting addon validation, or -1 to
        run with no timeout.
    `compat_tests`:
        A flag to signal the validator to skip tests which should not be run
        during compatibility bumps. Defaults to `False`.
    """

    bundle = ErrorBundle(listed=listed, determined=determined,
                         overrides=overrides, spidermonkey=spidermonkey,
                         for_appversions=for_appversions)
    bundle.save_resource("is_compat_test", compat_test)

    for name in 'approved_applications', 'library_metadata':
        # Accept overrides for app metadata as either a file path,
        # or a dict object. Update the appropriate constants.

        source = locals()[name]
        if source is not None:
            data = None
            if isinstance(source, types.StringTypes):
                # Load up the target applications if the approved
                # applications is a path (string).
                with open(source) as file:
                    data = json.load(file)
            elif isinstance(source, dict):
                # If the lists of approved applications are already in a
                # dict, just use that instead of trying to pull from a file.
                data = source

            if not isinstance(data, dict):
                raise ValueError("Unknown format for `%s`." % name)

            target = getattr(constants, name.upper())
            target.clear()
            target.update(data)

    submain.prepare_package(bundle, path, expectation,
                            for_appversions=for_appversions,
                            timeout=timeout)

    return format_result(bundle, format)


def format_result(bundle, format):
    # Write the results to the pipe
    formats = {"json": lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle
