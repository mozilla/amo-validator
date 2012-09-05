from collections import defaultdict
import hashlib
from itertools import imap
import json
import os
import pickle

import validator.decorator as decorator
from validator.constants import PACKAGE_EXTENSION
from validator.version import Version
from content import FLAGGED_FILES


SAFE_FILES = (".jpg", ".ico", ".png", ".gif", ".txt")

EMPTY_FILE_SHA256SUMS = ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495"
                         "991b7852b855")

JETPACK_DATA_FILE = os.path.join(os.path.dirname(__file__), "jetpack_data.txt")
JETPACK_PICKLE_FILE = JETPACK_DATA_FILE + ".pickle"

if os.path.exists(JETPACK_PICKLE_FILE):
    with open(JETPACK_PICKLE_FILE) as pickle_file:
        jetpack_hash_table = pickle.load(pickle_file)
        latest_jetpack = pickle.load(pickle_file)
else:
    # Read the jetpack data file in.
    with open(JETPACK_DATA_FILE) as jetpack_data:
        # Parse the jetpack data into something useful.
        jetpack_hash_table = defaultdict(dict)
        latest_jetpack = None
        for path, version_str, hash in imap(str.split, jetpack_data):
            version = Version(version_str)
            if version.is_release and (not latest_jetpack or
                                       version > latest_jetpack):
                latest_jetpack = version
            jetpack_hash_table[hash][version_str] = path

    with open(JETPACK_PICKLE_FILE, "w") as pickle_file:
        pickle.dump(jetpack_hash_table, pickle_file)
        pickle.dump(latest_jetpack, pickle_file)


@decorator.register_test(tier=1, expected_type=PACKAGE_EXTENSION)
def inspect_jetpack(err, xpi_package, allow_old_sdk=False):
    """
    If the add-on is a Jetpack extension, its contents should be tested to
    ensure that none of the Jetpack libraries have been tampered with.
    """

    jetpack_triggers = ("bootstrap.js", "harness-options.json")

    # Make sure this is a Jetpack add-on.
    if not all(trigger in xpi_package for trigger in jetpack_triggers):
        return

    try:
        harnessoptions = json.loads(xpi_package.read("harness-options.json"))
    except ValueError:
        err.warning(
            err_id=("testcases_jetpack",
                    "inspect_jetpack",
                    "bad_harness-options.json"),
            warning="harness-options.json is not decodable JSON",
            description="The harness-options.json file is not decodable as "
                        "valid JSON data.",
            filename="harness-options.json")
        return

    err.metadata["is_jetpack"] = True

    # Test the harness-options file for the mandatory values.
    mandatory_elements = ("sdkVersion", "manifest", "jetpackID")
    missing_elements = []
    for element in mandatory_elements:
        if element not in harnessoptions:
            missing_elements.append(element)

    if missing_elements:
        err.warning(
            err_id=("testcases_jetpack",
                    "inspect_jetpack",
                    "harness-options_missing_elements"),
            warning="Elements are missing from harness-options.json",
            description=["The harness-options.json file seems to be missing "
                         "elements. It may have been tampered with or is "
                         "corrupt.",
                         "Missing elements: %s" % ", ".join(missing_elements)],
            filename="harness-options.json")
        return

    # Save the SDK version information to the metadata.
    sdk_version = harnessoptions["sdkVersion"]
    err.metadata["jetpack_sdk_version"] = sdk_version

    # Check that the version number isn't a redacted version.
    if sdk_version in ("1.4", "1.4.1", "1.4.2", ):
        err.error(
            err_id=("testcases_jetpack", "inspect_jetpack",
                    "redacted_version"),
            error="Unsupported version of Add-on SDK",
            description="Versions 1.4, 1.4.1, and 1.4.2 of the add-on SDK may "
                        "cause issues with data loss in some modules. You "
                        "should upgrade the SDK to at least 1.4.3 in order to "
                        "avoid these issues.")

    # If we don't have a list of pretested files already, save a blank list.
    # Otherwise, use the existing list.
    pretested_files = err.get_resource("pretested_files")
    if not pretested_files:
        err.save_resource("pretested_files", [])
        pretested_files = []

    suppress_warnings = False
    if not allow_old_sdk and Version(sdk_version) < latest_jetpack:
        err.warning(
            err_id=("testcases_jetpack", "inspect_jetpack",
                    "outdated_version"),
            warning="Outdated version of Add-on SDK",
            description="You are using version %s of the Add-on SDK, "
                        "which is outdated. Please upgrade to version "
                        "%s and repack your add-on"
                            % (sdk_version, latest_jetpack))
    elif Version(sdk_version) > latest_jetpack:
        err.notice(
            err_id=("testcases_jetpack", "inspect_jetpack",
                    "future_version"),
            notice="Future version of Add-on SDK unrecognized",
            description="We've detected that the add-on uses a version of the "
                        "add-on SDK that we do not yet recognize.")
        suppress_warnings = True

    # Prepare a place to store mentioned hashes.
    found_hashes = set()

    loaded_modules = []
    tested_files = {}
    file_hashes = {}
    unknown_files = []
    mandatory_module_elements = ("moduleName", "packageName", "requirements",
                                 "sectionName", "docsSHA256", "jsSHA256")

    # Iterate each loaded module and perform a sha256 hash on the files.
    for uri, module in harnessoptions["manifest"].items():

        # Make sure the module is a resource:// URL
        if uri.startswith(("http://", "https://", "ftp://")):
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "irregular_module_location"),
                warning="Irregular Jetpack module location",
                description=["A Jetpack module is referenced with a remote "
                             "URI.",
                             "Referenced URI: %s" % uri],
                filename="harness-options.json")
            continue

        # Make sure all of the mandatory elements are present.
        if not all(el in module for el in mandatory_module_elements):
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "irregular_module_elements"),
                warning="Irregular Jetpack module elements",
                description=["A Jetpack module in harness-options.json is "
                             "missing some of its required JSON elements.",
                             "Module: %s" % uri],
                filename="harness-options.json")
            continue

        # Strip off the resource:// if it exists
        if uri.startswith("resource://"):
            uri = uri[11:]
        zip_path = "resources/%s" % uri.replace("@", "-at-")

        # Check the zipname element if it exists.
        if zip_path not in xpi_package:
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "missing_jetpack_module"),
                warning="Missing Jetpack module",
                description=["A Jetpack module listed in harness-options.json "
                             "could not be found in the add-on.",
                             "Path: %s" % zip_path],
                filename="harness-options.json")
            continue

        blob_hash = hashlib.sha256(xpi_package.read(zip_path)).hexdigest()
        file_hashes[zip_path] = blob_hash

        # Make sure that the module's hash matches what the manifest says.
        if blob_hash != module["jsSHA256"]:
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "mismatched_checksum"),
                warning="Jetpack module hash mismatch",
                description=["A file in the Jetpack add-on does not match the "
                             "corresponding hash listed in harness-options"
                             ".json.",
                             "Module: %s" % zip_path,
                             "Hashes: %s/%s" % (blob_hash, module["jsSHA256"])],
                filename=zip_path)

        # We aren't going to keep track of anything that isn't an official
        # Jetpack file.
        if module["jsSHA256"] not in jetpack_hash_table:
            continue

        # Keep track of all of the valid modules that were loaded.
        loaded_modules.append("".join([module["packageName"], "-",
                                       module["sectionName"], "/",
                                       module["moduleName"], ".js"]))

        # Save information on what was matched.
        tested_files[zip_path] = jetpack_hash_table[module["jsSHA256"]]
        pretested_files.append(zip_path)

    # Iterate the rest of the files in the package for testing.
    for filename in xpi_package:

        # Skip files we've already identified.
        if (filename in tested_files or
            filename == "harness-options.json"):
            continue

        # Skip safe files.
        if (filename.lower().endswith(SAFE_FILES) or
            filename in FLAGGED_FILES):
            continue

        blob_hash = (file_hashes.get(filename, None) or
                     hashlib.sha256(xpi_package.read(filename)).hexdigest())
        file_hashes[filename] = blob_hash

        if blob_hash not in jetpack_hash_table:
            unknown_files.append(filename)
            continue
        else:
            tested_files[filename] = jetpack_hash_table[blob_hash]
            pretested_files.append(filename)

        # Mark the hashes we actually find as being present.
        if blob_hash in found_hashes:
            found_hashes.discard(blob_hash)

    # Store the collected information in the output metadata.
    err.save_resource("pretested_files", pretested_files)
    err.metadata["jetpack_loaded_modules"] = loaded_modules
    err.metadata["jetpack_unknown_files"] = unknown_files

    if suppress_warnings:
        return

    for zip_path, versions in tested_files.items():
        if sdk_version in versions:
            tested_files[zip_path] = sdk_version, versions[sdk_version]
        else:
            # This isn't the version it claims to be. Go with the latest
            # Jetpack version we know about that contains it.
            version = str(max(map(Version, versions.keys())))
            tested_files[zip_path] = version, versions[version]

            if (file_hashes[zip_path] not in EMPTY_FILE_SHA256SUMS and
                not zip_path.endswith("/")):
                err.warning(
                    err_id=("testcases_jetpack",
                            "inspect_jetpack",
                            "mismatched_version"),
                    warning="Jetpack module version mismatch",
                    description=["A file in the Jetpack add-on does not match "
                                 "the SDK version specified in harness-options"
                                 ".json.",
                                 "Module: %s" % zip_path,
                                 "Versions: %s/%s" % (sdk_version, version)],
                    filename=zip_path)

    # We've got hashes left over
    if found_hashes:
        err.warning(
            err_id=("testcases_jetpack", "inspect_jetpack", "extra_hashes"),
            warning="Extra hashes registered in harness-options.",
            description=["This Jetpack add-on registers modules in the "
                         "harness-options.json file that do not exist in the "
                         "package.",
                         "Hashes: %s" % ", ".join(found_hashes)],
            filename="harness-options.json")

    # Store the collected information in the output metadata.
    err.metadata["jetpack_identified_files"] = tested_files

