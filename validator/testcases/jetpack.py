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
        metadata_validator = HarnessOptionsValidator(
            err, xpi_package, allow_old_sdk)
        if not metadata_validator.is_valid():
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


class HarnessOptionsValidator(object):
    def __init__(self, err, xpi, allow_old_sdk):
        self.err = err
        self.xpi = xpi
        self.allow_old_sdk = allow_old_sdk
        self.tested_files = {}
        self.file_hashes = {}
        self.suppress_warnings = False
        self.use_latest_version = False

    def is_valid(self):
        try:
            harnessoptions = json.loads(self.xpi.read('harness-options.json'))
        except ValueError:
            self.err.warning(
                err_id=('testcases_jetpack',
                        'inspect_jetpack',
                        'bad_harness-options.json'),
                warning='harness-options.json is not decodable JSON',
                description='The harness-options.json file is not decodable '
                            'as valid JSON data.',
                filename='harness-options.json')
            return

        # Test the harness-options file for the mandatory values.
        mandatory_elements = ('sdkVersion', 'manifest', 'jetpackID')
        missing_elements = []
        for element in mandatory_elements:
            if element not in harnessoptions:
                missing_elements.append(element)

        if missing_elements:
            self.err.warning(
                err_id=('testcases_jetpack',
                        'inspect_jetpack',
                        'harness-options_missing_elements'),
                warning='Elements are missing from harness-options.json',
                description=('The harness-options.json file seems to be '
                             'missing elements. It may have been tampered '
                             'with or is corrupt.',
                             'Missing elements: %s'
                             % ', '.join(missing_elements)),
                filename='harness-options.json')
            return

        # Save the SDK version information to the metadata.
        sdk_version = harnessoptions['sdkVersion']
        self.err.metadata['jetpack_sdk_version'] = sdk_version

        # Check that the version number isn't a redacted version.
        if sdk_version in ('1.4', '1.4.1', '1.4.2', ):
            self.err.error(
                err_id=('testcases_jetpack', 'inspect_jetpack',
                        'redacted_version'),
                error='Unsupported version of Add-on SDK',
                description='Versions 1.4, 1.4.1, and 1.4.2 of the add-on SDK '
                            'may cause issues with data loss in some modules. '
                            'You should upgrade the SDK to at least 1.4.3 in '
                            'order to avoid these issues.')

        pretested_files = self.err.get_resource('pretested_files')

        if not self.allow_old_sdk and Version(sdk_version) < latest_jetpack:
            self.err.warning(
                err_id=('testcases_jetpack', 'inspect_jetpack',
                        'outdated_version'),
                warning='Outdated version of Add-on SDK',
                description='You are using version %s of the Add-on SDK, '
                            'which is outdated. Please upgrade to version '
                            '%s and repack your add-on'
                            % (sdk_version, latest_jetpack))
        elif Version(sdk_version) > latest_jetpack:
            self.err.notice(
                err_id=('testcases_jetpack', 'inspect_jetpack',
                        'future_version'),
                notice='Future version of Add-on SDK unrecognized',
                description="We've detected that the add-on uses a version of "
                            'the add-on SDK that we do not yet recognize.')
            self.suppress_warnings = True

        loaded_modules = []
        mandatory_module_elements = (
            'moduleName', 'packageName', 'requirements', 'sectionName',
            'docsSHA256', 'jsSHA256')

        # Iterate each loaded module and perform a sha256 hash on the files.
        for uri, module in harnessoptions['manifest'].items():

            # Make sure the module is a resource:// URL
            if uri.startswith(('http://', 'https://', 'ftp://')):
                self.err.warning(
                    err_id=('testcases_jetpack',
                            'inspect_jetpack',
                            'irregular_module_location'),
                    warning='Irregular Jetpack module location',
                    description=('A Jetpack module is referenced with a '
                                 'remote URI.',
                                 'Referenced URI: %s' % uri),
                    filename='harness-options.json')
                continue

            # Make sure all of the mandatory elements are present.
            if not all(el in module for el in mandatory_module_elements):
                self.err.warning(
                    err_id=('testcases_jetpack',
                            'inspect_jetpack',
                            'irregular_module_elements'),
                    warning='Irregular Jetpack module elements',
                    description=('A Jetpack module in harness-options.json is '
                                 'missing some of its required JSON elements.',
                                 'Module: %s' % uri),
                    filename='harness-options.json')
                continue

            # Strip off the resource:// if it exists
            if uri.startswith('resource://'):
                uri = uri[11:]
            zip_path = 'resources/%s' % uri.replace('@', '-at-')

            # The key is no longer a URI in newer versions of the SDK
            if zip_path not in self.xpi:
                zip_path = 'resources/%s/%s/%s.js' % (
                    module['packageName'], module['sectionName'],
                    module['moduleName'])

            # Check the zipname element if it exists.
            if zip_path not in self.xpi:
                self.err.warning(
                    err_id=('testcases_jetpack',
                            'inspect_jetpack',
                            'missing_jetpack_module'),
                    warning='Missing Jetpack module',
                    description=('A Jetpack module listed in '
                                 'harness-options.json could not be found in '
                                 'the add-on.',
                                 'Path: %s' % zip_path),
                    filename='harness-options.json')
                continue

            file_data = self.xpi.read(zip_path)
            if not file_data.strip():
                continue
            blob_hash = hashlib.sha256(file_data).hexdigest()
            self.file_hashes[zip_path] = blob_hash

            # Make sure that the module's hash matches what the manifest says.
            if blob_hash != module['jsSHA256']:
                self.err.warning(
                    err_id=('testcases_jetpack',
                            'inspect_jetpack',
                            'mismatched_checksum'),
                    warning='Jetpack module hash mismatch',
                    description=('A file in the Jetpack add-on does not match '
                                 'the corresponding hash listed in '
                                 'harness-options.json.',
                                 'Module: %s' % zip_path,
                                 'Hashes: %s/%s'
                                 % (blob_hash, module['jsSHA256'])),
                    filename=zip_path)

            # We aren't going to keep track of anything that isn't an official
            # Jetpack file.
            if module['jsSHA256'] not in jetpack_hash_table:
                continue

            # Keep track of all of the valid modules that were loaded.
            loaded_modules.append(''.join([module['packageName'], '-',
                                           module['sectionName'], '/',
                                           module['moduleName'], '.js']))

            # Save information on what was matched.
            self.tested_files[zip_path] = jetpack_hash_table[
                module['jsSHA256']]
            pretested_files.append(zip_path)

        self.err.save_resource('pretested_files', pretested_files)
        self.err.metadata['jetpack_loaded_modules'] = loaded_modules

        return True


class PackageJsonValidator(object):
    def __init__(self, err, xpi_package):
        self.tested_files = {}
        self.file_hashes = {}
        self.suppress_warnings = False
        self.use_latest_version = True
