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


SAFE_FILES = ('.jpg', '.ico', '.png', '.gif', '.txt')

JETPACK_DATA_FILE = os.path.join(os.path.dirname(__file__), 'jetpack_data.txt')
JETPACK_PICKLE_FILE = JETPACK_DATA_FILE + '.pickle'

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

    with open(JETPACK_PICKLE_FILE, 'w') as pickle_file:
        pickle.dump(jetpack_hash_table, pickle_file)
        pickle.dump(latest_jetpack, pickle_file)


@decorator.register_test(tier=1, expected_type=PACKAGE_EXTENSION)
def inspect_jetpack(err, xpi_package, allow_old_sdk=False):
    """
    If the add-on is a Jetpack extension, its contents should be tested to
    ensure that none of the Jetpack libraries have been tampered with.
    """

    if not is_jetpack(xpi_package):
        return

    err.metadata['is_jetpack'] = True
    if not err.get_resource('pretested_files'):
        err.save_resource('pretested_files', [])

    if is_old_jetpack(xpi_package):
        # Ignore this test for cfx based add-ons if run as part of bulk
        # validation because existing add-ons on AMO have been re-packed.
        # We just need this for validation during upload.
        if err.get_resource('is_compat_test'):
            return
        err.error(
            err_id=('jetpack', 'inspect_jetpack',
                    'cfx'),
            error='Add-ons built with "cfx" are no longer accepted.',
            description='Due to breaking changes in Firefox 44, add-ons packed '
                        'with the "cfx" tool won\'t work any longer. To make '
                        'your add-on compatible again, please use the "jpm" '
                        'tool (http://mzl.la/1PwF5fY). You can find steps to '
                        'migrate from "cfx" to "jpm" at http://mzl.la/1ncmH3A')
        return
    else:
        metadata_validator = PackageJsonValidator(err, xpi_package)

    # Prepare a place to store mentioned hashes.
    found_hashes = set()
    unknown_files = []
    tested_files = metadata_validator.tested_files
    file_hashes = metadata_validator.file_hashes
    pretested_files = err.get_resource('pretested_files')

    # Iterate the rest of the files in the package for testing.
    for filename in xpi_package:

        # Skip files we've already identified.
        if (filename in tested_files or
                filename == 'harness-options.json'):
            continue

        # Skip safe files.
        if (filename.lower().endswith(SAFE_FILES) or
                filename in FLAGGED_FILES):
            continue

        file_data = xpi_package.read(filename)
        # Skip empty files.
        if not file_data.strip():
            continue
        blob_hash = (file_hashes.get(filename, None) or
                     hashlib.sha256(file_data).hexdigest())
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
    err.save_resource('pretested_files', pretested_files)
    err.metadata['jetpack_unknown_files'] = unknown_files

    if metadata_validator.suppress_warnings:
        return

    sdk_version = err.metadata.get('jetpack_sdk_version')
    for zip_path, versions in tested_files.items():
        if sdk_version in versions:
            tested_files[zip_path] = sdk_version, versions[sdk_version]
        else:
            # This isn't the version it claims to be. Go with the latest
            # Jetpack version we know about that contains it.
            version = str(max(Version(v) for v in versions))
            tested_files[zip_path] = version, versions[version]

            if (not zip_path.endswith('/') and
                    not metadata_validator.use_latest_version):
                err.warning(
                    err_id=('testcases_jetpack',
                            'inspect_jetpack',
                            'mismatched_version'),
                    warning='Jetpack module version mismatch',
                    description=('A file in the Jetpack add-on does not match '
                                 'the SDK version specified in harness-options'
                                 '.json.',
                                 'Module: %s' % zip_path,
                                 'Versions: %s/%s' % (sdk_version, version)),
                    filename=zip_path)

    # We've got hashes left over
    if found_hashes:
        err.warning(
            err_id=('testcases_jetpack', 'inspect_jetpack', 'extra_hashes'),
            warning='Extra hashes registered in harness-options.',
            description=('This Jetpack add-on registers modules in the '
                         'harness-options.json file that do not exist in the '
                         'package.',
                         'Hashes: %s' % ', '.join(found_hashes)),
            filename='harness-options.json')

    # Store the collected information in the output metadata.
    err.metadata['jetpack_identified_files'] = tested_files

    identified_files = err.metadata.setdefault('identified_files', {})

    for file, (version, path) in tested_files.items():
        identified_files[file] = {'path': path, 'version': version,
                                  'library': 'Jetpack'}


def is_jetpack(xpi):
    return has_bootstrap(xpi) and (has_harness_options(xpi) or
                                   has_package_json(xpi))


def is_old_jetpack(xpi):
    return has_bootstrap(xpi) and has_harness_options(xpi)


def has_bootstrap(xpi):
    return 'bootstrap.js' in xpi


def has_harness_options(xpi):
    return 'harness-options.json' in xpi


def has_package_json(xpi):
    return 'package.json' in xpi


class PackageJsonValidator(object):
    def __init__(self, err, xpi_package):
        self.tested_files = {}
        self.file_hashes = {}
        self.suppress_warnings = False
        self.use_latest_version = True
