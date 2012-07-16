import json
import os
import types

from . import constants
from .constants import PACKAGE_ANY, PACKAGE_WEBAPP
from errorbundler import ErrorBundle
import loader
import submain
import webapp


def validate(path, format="json",
             approved_applications=os.path.join(os.path.dirname(__file__),
                                                "app_versions.json"),
             determined=True,
             spidermonkey=False,
             listed=True,
             expectation=PACKAGE_ANY,
             for_appversions=None,
             overrides=None,
             timeout=None,
             market_urls=None,
             compat_test=False):
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
    `spidermonkey`:
        Path to the local spidermonkey installation. Defaults to `False`, which
        uses the validator's built-in detection of Spidermonkey. Specifying
        `None` will disable JavaScript tests. Any other value is treated as the
        path.
    `listed`:
        Whether the app is headed for the app marketplace or AMO. Defaults to
        `True`.
    `expectation`:
        The type of package that should be expected. Must be a symbolic constant
        from validator.constants (i.e.: validator.constants.PACKAGE_*). Defaults
        to PACKAGE_ANY.
    `for_appversions`:
        A dict of app GUIDs referencing lists of versions. Determines which
        version-dependant tests should be run.
    `timeout`:
        Number of seconds before aborting addon validation.
    `market_urls`:
        A list of URLs used for validating the `installs_allowed_from` property
        of webapp manifests.
    `compat_tests`:
        A flag to signal the validator to skip tests which should not be run
        during compatibility bumps. Defaults to `False`.
    """

    bundle = ErrorBundle(listed=listed, determined=determined,
                         overrides=overrides, spidermonkey=spidermonkey,
                         for_appversions=for_appversions)
    bundle.save_resource("is_compat_test", compat_test)

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
        raise ValueError("Unknown format for `approved_applications`.")

    constants.APPROVED_APPLICATIONS.clear()
    constants.APPROVED_APPLICATIONS.update(apps)

    # Set the marketplace URLs if they're provided.
    set_market_urls(market_urls)

    submain.prepare_package(bundle, path, expectation,
                            for_appversions=for_appversions,
                            timeout=timeout)

    return format_result(bundle, format)


def validate_app(data, listed=True, market_urls=None):
    """
    A handy function for validating apps.

    `data`:
        A copy of the manifest as a JSON string.
    `listed`:
        Whether the app is headed for the app marketplace.
    `market_urls`:
        A list of URLs to use when validating the `installs_allowed_from`
        field of the manifest. Does not apply if `listed` is not set to `True`.

    Notes:
    - App validation is always determined because there is only one tier.
    - Spidermonkey paths are not accepted by this function because we don't
      perform JavaScript validation on webapps.
    - We don't accept a flag for compatibility because there are no
      compatibility tests for apps, nor will there likely ever be. The same
      goes for associated parameters (i.e.: for_appversions).
    - `approved_applications` is not set because apps are not bound to
      individual Mozilla apps.
    """
    bundle = ErrorBundle(listed=listed, determined=True)

    # Set the market URLs.
    set_market_urls(market_urls)

    webapp.detect_webapp_string(bundle, data)
    return format_result(bundle, "json")


def format_result(bundle, format):
    # Write the results to the pipe
    formats = {"json": lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle


def set_market_urls(market_urls=None):
    if market_urls is not None:
        constants.DEFAULT_WEBAPP_MRKT_URLS = market_urls

