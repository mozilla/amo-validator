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


def validate(path, format='json',
             approved_applications=None,
             determined=True,
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
        Path to the list of approved application versions
    `determined`:
        If set to `False`, validation will halt at the end of the first tier
        that raises errors.
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
                         overrides=overrides, for_appversions=for_appversions)
    bundle.save_resource('is_compat_test', compat_test)

    if approved_applications is None:
        approved_applications = os.path.join(os.path.dirname(__file__),
                                             'app_versions.json')

    if isinstance(approved_applications, types.StringTypes):
        # Load up the target applications if the approved applications is a
        # path (string).
        with open(approved_applications) as approved_apps:
            apps = json.load(approved_apps)
    elif isinstance(approved_applications, dict):
        # If the lists of approved applications are already in a dict, just use
        # that instead of trying to pull from a file.
        apps = approved_applications
    else:
        raise ValueError('Unknown format for `approved_applications`.')

    constants.APPROVED_APPLICATIONS.clear()
    constants.APPROVED_APPLICATIONS.update(apps)

    submain.prepare_package(bundle, path, expectation,
                            for_appversions=for_appversions,
                            timeout=timeout)

    return format_result(bundle, format)


def format_result(bundle, format):
    # Write the results to the pipe
    formats = {'json': lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle
