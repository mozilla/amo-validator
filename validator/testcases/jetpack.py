import hashlib
import json
import os
import validator.decorator as decorator
from validator.constants import PACKAGE_EXTENSION


@decorator.register_test(tier=1, expected_type=PACKAGE_EXTENSION)
def inspect_jetpack(err, xpi_package):
    """
    If the add-on is a Jetpack extension, its contents should be tested to
    ensure that none of the Jetpack libraries have been tampered with.
    """

    jetpack_triggers = ("bootstrap.js",
                        "components/harness.js",
                        "harness-options.json")

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
    mandatory_elements = ("sdkVersion", "manifest")
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
    err.metadata["jetpack_sdk_version"] = harnessoptions["sdkVersion"]
    pretested_files = err.get_resource("pretested_files")
    if not pretested_files:
        err.save_resource("pretested_files", [])
        pretested_files = []

    # Read the jetpack data file in.
    jetpack_data = open(os.path.join(os.path.dirname(__file__),
                                     "jetpack_data.txt"))
    # Parse the jetpack data into something useful.
    jetpack_hash_table = {}
    for line in map(lambda x: x.split(), jetpack_data):
        jetpack_hash_table[line[-1]] = tuple(line[:-1])

    loaded_modules = []
    tested_files = {}
    unknown_files = []
    mandatory_module_elements = ("name", "hash", "zipname")

    # Iterate each loaded module and perform a sha256 hash on the files.
    for uri, module in harnessoptions["manifest"].items():

        # Make sure the module is a resource:// URL
        if not uri.startswith("resource://"):
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "irregular_module_location"),
                warning="Irregular Jetpack module location",
                description="A Jetpack module is referenced with a non-"
                            "resource URI.",
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

        zip_path = module["zipname"]

        # Make sure that the module actually exists in the add-on.
        if zip_path not in xpi_package:
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "missing_jetpack_module"),
                warning="Missing Jetpack module",
                description=["A Jetpack module listed in harness-options.json "
                             "could not be found in the add-on.",
                             "Path: %s" % module["zipname"]],
                filename="harness-options.json")
            continue

        blob = xpi_package.read(zip_path)
        blob_hash = hashlib.sha256(blob).hexdigest()

        if blob_hash != module["hash"]:
            # Warn that the hashes don't match up.
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "mismatched_checksum"),
                warning="Jetpack module hash mismatch",
                description=["A file in the Jetpack add-on does not match the "
                             "corresponding hash listed in harness-options"
                             ".json.",
                             "Module: %s" % uri,
                             "Hashes: %s/%s" % (blob_hash, module["hash"])],
                filename=zip_path)
            continue

        if blob_hash not in jetpack_hash_table:
            # Warn that the hash isn't a valid jetpack hash.
            err.warning(
                err_id=("testcases_jetpack",
                        "inspect_jetpack",
                        "unknown_hash"),
                warning="Jetpack module hash unknown",
                description=["A file in the Jetpack add-on could not be "
                             "identified in the Jetpack SDK checksum "
                             "database. The file may have been tampered with.",
                             "Module: %s" % uri,
                             "Hash: %s" % blob_hash],
                filename=zip_path)
            continue

        # Keep track of all of the valid modules that were loaded.
        loaded_modules.append(module["name"])

        # Save information on what was matched.
        tested_files[zip_path] = jetpack_hash_table[blob_hash]
        pretested_files.append(zip_path)

    safe_files = (".jpg", ".ico", ".png", ".gif", ".ds_store")

    # Iterate the rest of the files in the package for testing.
    for filename in xpi_package:

        # Skip files we've already identified.
        if (filename in tested_files or
            filename == "harness-options.json"):
            continue

        # Skip safe files.
        if filename.lower().endswith(safe_files):
            continue

        blob = xpi_package.read(filename)
        blob_hash = hashlib.sha256(blob).hexdigest()

        if blob_hash not in jetpack_hash_table:
            unknown_files.append(filename)
            continue
        else:
            tested_files[filename] = jetpack_hash_table[blob_hash]
            pretested_files.append(filename)

    # Store the collected information in the output metadata.
    err.metadata["jetpack_loaded_modules"] = loaded_modules
    err.metadata["jetpack_identified_files"] = tested_files
    err.metadata["jetpack_unknown_files"] = unknown_files

    err.save_resource("pretested_files", pretested_files)

