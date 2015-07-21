import hashlib
import json
import re

from validator.constants import DEPRECATED_HARD, LIBRARY_METADATA
from validator.decorator import cached_property
from validator.testcases import libraries
from validator.version import Version


def fake_version(files):
    """
    Returns a hash to act in place of a version number, given the contents
    of a set of known files.
    """
    return hashlib.sha256("".join(files)).hexdigest()[:16]


class MetaFramework(type):
    def __new__(mcls, name, bases, dict_):
        cls = super(MetaFramework, mcls).__new__(mcls, name, bases, dict_)
        if cls.NAME:
            cls.FRAMEWORKS.append(cls)
        return cls


class Framework(object):
    """
    Base class for framework definitions.
    """

    FRAMEWORKS = []

    SAFE_FILES = ".jpg", ".ico", ".png", ".gif", ".txt"

    CHECKED_FILES = re.compile(r"\.(jsm?|xul|xbl|x?html?)$", re.I)

    NAME = None
    ACCEPTED = True

    # Path of the JSON file within the XPI containing framework
    # metadata. Not applicable to all frameworks.
    METADATA_FILE = None

    # Tuple of file paths which, if they exist, belong to the framework.
    FRAMEWORK_FILES = ()

    # Tuple of file path prefixes for which matching files, if they
    # exist, belong to the framework.
    FRAMEWORK_PREFIXES = ()

    __metaclass__ = MetaFramework

    def __init__(self, err, xpi):
        self.err = err
        self.xpi = xpi

        # Update certain metadata from the metadata JSON.
        # Ideally this would also update based on data for the
        # specific version of the framework, but there are
        # bootstrapping issues.
        for prop in "framework_files", "framework_prefixes":
            if prop in self.framework_metadata:
                setattr(self, prop.upper(),
                        tuple(self.framework_metadata[prop]))

    @cached_property
    def ID(self):
        """Internal ID of the framework."""
        return self.NAME.lower()

    def detect(self):
        """Returns true if the add-on matches the given framework."""
        raise NotImplementedError

    @property
    def framework_metadata(self):
        """
        Returns the metadata for this framework, as defined in the
        libraries metadata file if it exists, or a resonable
        skeleton definition if it does not.
        """
        DEFAULT = {"versions": {}}

        return LIBRARY_METADATA["frameworks"].get(self.ID, DEFAULT)

    @cached_property
    def framework_files(self):
        """
        Returns a list of files in the package which belong to the framework
        in question. Files may or may not match known versions of the file.
        """
        return (filter(self.xpi.__contains__, list(self.FRAMEWORK_FILES)) +
                [f for f in self.xpi
                 if (f.startswith(self.FRAMEWORK_PREFIXES) and
                     not f.endswith("/"))])

    @cached_property
    def metadata(self):
        """
        Returns the parsed JSON content of the framework's metadata file, if
        applicable, and the contents are sane. Otherwise returns `None`.
        """
        if self.METADATA_FILE and self.METADATA_FILE in self.xpi:
            try:
                metadata = json.loads(self.xpi.read(self.METADATA_FILE))
                if isinstance(metadata, dict):
                    return metadata
            except:
                pass

    def get_fake_version(self):
        """
        No version number? This is unfortunate. We need to be able
        to keep track of versions, so just glom together a hash of
        framework files.
        """
        return fake_version(self.xpi.read(f)
                            for f in sorted(self.framework_files)
                            if self.CHECKED_FILES.search(f))

    @cached_property
    def version(self):
        """
        Returns the version of the framework used, or a fake version number
        based on the contents of framework files if not known.
        """
        # Try to find a version common to all framework files, then
        # fall back to a hash-based version ID.

        identities = map(self.err.metadata["identified_files"].get,
                         filter(self.CHECKED_FILES.search,
                                self.framework_files))

        return (libraries.identify_files(identities, self.ID) or
                self.get_fake_version())

    def error(self, *args, **kw):
        """
        Adds an error to the error bundle, and marks the framework as
        invalid.
        """
        self.valid = False
        self.err.error(*args, **kw)

    def validate(self):
        """
        Perform basic validation of the framework, including checking that
        all framework files match known checksums, and that the framework
        and framework version are currently accepted.
        """

        # Assume valid at the start. Set to False when errors are
        # detected.
        self.valid = True

        if self.METADATA_FILE and self.metadata is None:
            self.error(
                err_id=("testcases_frameworks",
                        "invalid_metadata"),
                error="Invalid metadata file",
                description=("This add-on does not contain a valid metadata "
                             "file for the %s framework."
                             % self.NAME),
                filename=self.METADATA_FILE)

            return self.valid

        self.err.metadata["framework"] = {"name": self.NAME,
                                          "id": self.ID,
                                          "version": self.version}

        metadata = self.framework_metadata

        version_metadata = metadata.get("versions", {}).get(self.version, {})

        messages = (metadata.get("messages", [])
                    + version_metadata.get("messages", []))

        deprecated = metadata.get("deprecated",
                                  DEPRECATED_HARD if not self.ACCEPTED else 0)
        if deprecated:
            report = (self.err.warning if deprecated < DEPRECATED_HARD
                      else self.error)
            report(
                err_id=("testcases_frameworks", "deprecated_framework"),
                message="Deprecated add-on framework in use",
                description=(["This extension makes use of the %s framework, "
                              "which is not currently accepted for use on AMO"
                              % self.NAME]
                             + messages))

        elif not version_metadata:
            self.error(
                err_id=("testcases_frameworks", "unknown_framework_version"),
                error="Unknown framework version",
                description=(["You are using version %s of the %s framework, "
                              "which is currently unknown and not accepted."
                              % (self.version, self.NAME)]
                             + messages))

        elif version_metadata.get("deprecated"):
            deprecated = version_metadata["deprecated"]
            report = (self.err.warning if deprecated < DEPRECATED_HARD
                      else self.error)
            report(
                err_id=("testcases_frameworks",
                        "deprecated_framework_version"),
                message="Deprecated framework version",
                description=(["You are using version %s of the %s framework, "
                              "which is currently known but not accepted."
                              % (self.version, self.NAME)]
                             + messages))

        elif messages:
            self.err.notice(
                err_id=("testcases_frameworks",
                        "detected_framework"),
                notice="Add-on framework detected",
                description=(["This add-on is using the %s framework."
                              % self.NAME]
                             + messages))

        identified = self.err.metadata.setdefault("identified_files", {})

        tag = [self.ID, self.version]
        for path in self.framework_files:
            if not self.CHECKED_FILES.search(path):
                continue

            identity = identified.get(path)
            if not identity:
                # This may turn out to be something we want:
                # Skip checks on framework files even if not identified
                # by hash.
                # identified[path] = {"deprecated": DEPRECATED_HARD}

                self.error(
                    err_id=("testcases_frameworks", "unknown_file"),
                    error="Unknown framework file",
                    description=("A file belonging to the %s framework does "
                                 "not match any known checksum." % self.NAME),
                    filename=path)

            elif not any(match[0:2] == tag for match in identity["sources"]):
                # None of this files sources are from this version
                # of this framework. Report mismatch.

                version = (libraries.identify_files([identity], self.ID)
                           or "unknown")

                self.error(
                    err_id=("testcases_frameworks",
                            "incorrect_file_version"),
                    error="Incorrect framework file version",
                    description=("A file belonging to the %s framework does "
                                 "not match the expected framework version."
                                 % self.NAME,
                                 "Expected %s, got %s."
                                 % (self.version, version)),
                    filename=path)

        self.err.metadata["framework_files"] = self.framework_files

        return self.valid

    @classmethod
    def detect_framework(cls, err, xpi):
        for framework in cls.FRAMEWORKS:
            f = framework(err, xpi)
            if f.detect():
                f.validate()
                return f


class BestToolbars(Framework):
    NAME = "Besttoolbars"
    METADATA_FILE = "chrome/content/config.json"

    FRAMEWORK_FILES = ("chrome/content/ci.options.js",
                       "chrome/content/framework.js",
                       "chrome/content/subscriptloader.js",
                       "chrome/content/config.json")

    def detect(self):
        FILE = "chrome/content/framework.js"
        return (FILE in self.xpi and
                "besttoolbars" in self.xpi.read(FILE))


class Conduit(Framework):
    NAME = "Conduit"
    ACCEPTED = False

    def detect(self):
        return ("searchplugins/conduit.xml" in self.xpi and
                any(f.startswith("components/Conduit")
                    for f in self.xpi))


class Crossrider(Framework):
    NAME = "Crossrider"
    ACCEPTED = False

    def detect(self):
        return any(f in self.xpi
                   for f in (
                       "chrome/content/CrossriderEXT.js",
                       "chrome/content/crossrider.js",
                       "chrome/content/crossriderapi.js"))


class JetpackBase(Framework):
    """Abstract base class for Jetpack-based frameworks."""

    def detect(self):
        return all(f in self.xpi
                   for f in self.FRAMEWORK_FILES)

    def validate(self):
        if not super(JetpackBase, self).validate():
            return self.valid

        # Legacy
        self.err.metadata["is_jetpack"] = True

        return self.valid


# Built on top of Jetpack, so must come first.
class OpenForge(JetpackBase):
    NAME = "OpenForge"
    ACCEPTED = False

    def detect(self):
        return "resources/f/data/forge/all.js" in self.xpi


class JetpackCFX(JetpackBase):
    NAME = "Jetpack"
    ID = "jetpack"
    METADATA_FILE = "harness-options.json"

    FRAMEWORK_FILES = ("bootstrap.js",
                       "harness-options.json")

    FRAMEWORK_PREFIXES = (
        "resources/addon-sdk/",
        # The following were used in old versions of the
        # SDK. Mostly still checked for legacy reasons,
        # given that these versions are no longer
        # accepted.
        "resources/api-utils/",
        "resources/addon-kit/",
    )

    @cached_property
    def version(self):
        return self.metadata.get("sdkVersion")

    def validate(self):
        """
        Perform SDK-specific validation.
        """
        import hashlib

        if not super(JetpackCFX, self).validate():
            # If we already know this isn't valid, don't bother with
            # further tests.
            return False

        latest_jetpack = max(Version(v)
                             for v in (self.framework_metadata["versions"]
                                           .keys())
                             if Version(v).is_release)

        # Test the harness-options file for the mandatory values.
        mandatory_elements = set(("sdkVersion", "manifest", "jetpackID"))
        missing_elements = mandatory_elements - set(self.metadata)

        if missing_elements:
            self.error(
                err_id=("testcases_frameworks",
                        "validate_jetpack_cfx",
                        "harness-options_missing_elements"),
                error="Elements are missing from harness-options.json",
                description=("The harness-options.json file seems to be "
                             "missing elements. It may have been tampered "
                             "with or is corrupt.",
                             "Missing elements: %s"
                             % ", ".join(missing_elements)),
                filename=self.METADATA_FILE)
            return self.valid

        # Legacy.
        self.err.metadata["jetpack_sdk_version"] = self.version

        identified_files = self.err.metadata.get("identified_files")

        if Version(self.version) < latest_jetpack:
            self.err.warning(
                err_id=("testcases_frameworks", "validate_jetpack_cfx",
                        "outdated_version"),
                warning="Outdated version of Add-on SDK",
                description="You are using version %s of the Add-on SDK, "
                            "which is outdated. Please upgrade to version "
                            "%s and repack your add-on"
                            % (self.version, latest_jetpack))
        elif Version(self.version) > latest_jetpack:
            # We've probably already rejected the add-on for
            # unrecognized framework files at this point.
            self.err.notice(
                err_id=("testcases_frameworks", "validate_jetpack_cfx",
                        "future_version"),
                notice="Future version of Add-on SDK unrecognized",
                description="We've detected that the add-on uses a version of "
                            "the add-on SDK that we do not yet recognize.")

        loaded_modules = []
        mandatory_module_elements = (
            "moduleName", "packageName", "requirements", "sectionName",
            "docsSHA256", "jsSHA256")

        # Iterate each loaded module and perform a sha256 hash on the files.
        for uri, module in self.metadata["manifest"].items():
            # Make sure the module is a resource:// URL
            if uri.startswith(("http://", "https://", "ftp://")):
                self.err.warning(
                    err_id=("testcases_frameworks",
                            "validate_jetpack_cfx",
                            "irregular_module_location"),
                    warning="Irregular Jetpack module location",
                    description=("A Jetpack module is referenced with a "
                                 "remote URI.",
                                 "Referenced URI: %s" % uri),
                    filename="harness-options.json")
                continue

            # Make sure all of the mandatory elements are present.
            if not all(el in module for el in mandatory_module_elements):
                self.err.warning(
                    err_id=("testcases_frameworks",
                            "validate_jetpack_cfx",
                            "irregular_module_elements"),
                    warning="Irregular Jetpack module elements",
                    description=("A Jetpack module in harness-options.json is "
                                 "missing some of its required JSON elements.",
                                 "Module: %s" % uri),
                    filename="harness-options.json")
                continue

            # Strip off the resource:// if it exists
            if uri.startswith("resource://"):
                uri = uri[len("resource://"):]

            zip_path = "resources/%s" % uri.replace("@", "-at-")

            # The key is no longer a URI in newer versions of the SDK
            if zip_path not in self.xpi:
                zip_path = "resources/%s/%s/%s.js" % (
                    module["packageName"], module["sectionName"],
                    module["moduleName"])

            # Check the zipname element if it exists.
            if zip_path not in self.xpi:
                self.err.warning(
                    err_id=("testcases_frameworks",
                            "validate_jetpack_cfx",
                            "missing_jetpack_module"),
                    warning="Missing Jetpack module",
                    description=("A Jetpack module listed in "
                                 "harness-options.json could not be found in "
                                 "the add-on.",
                                 "Path: %s" % zip_path),
                    filename="harness-options.json")
                continue

            file_data = self.xpi.read(zip_path)
            if not file_data.strip():
                # Skip empty files
                continue

            # Make sure that the module's hash matches what the manifest says.
            blob_hash = hashlib.sha256(file_data).hexdigest()
            if blob_hash != module["jsSHA256"]:
                self.err.warning(
                    err_id=("testcases_frameworks",
                            "validate_jetpack_cfx",
                            "mismatched_checksum"),
                    warning="Jetpack module hash mismatch",
                    description=("A file in the Jetpack add-on does not match "
                                 "the corresponding hash listed in "
                                 "harness-options.json.",
                                 "Module: %s" % zip_path,
                                 "Hashes: %s/%s"
                                 % (blob_hash, module["jsSHA256"])),
                    filename=zip_path)

            # We aren't going to keep track of anything that isn't an official
            # Jetpack file.
            identity = identified_files.get(zip_path)
            if identity and "jetpack" in (s[0] for s in identity["sources"]):
                # Keep track of all of the valid modules that were loaded.
                loaded_modules.append("%(packageName)s-%(sectionName)s/"
                                      "%(moduleName)s.js" % module)

        self.err.metadata["jetpack_loaded_modules"] = loaded_modules
        return self.valid


class JetpackJPM(JetpackBase):
    NAME = "Jetpack (JPM)"
    ID = "jetpack-jpm"
    METADATA_FILE = "package.json"

    FRAMEWORK_FILES = ("bootstrap.js",
                       "package.json")


class Kango(Framework):
    NAME = "Kango"
    METADATA_FILE = "extension_info.json"

    def detect(self):
        return self.metadata and "kango_version" in self.metadata

    FRAMEWORK_FILES = ("bootstrap.js",
                       "extension_info.json")

    FRAMEWORK_PREFIXES = ("kango/",
                          "kango-ui/")

    @cached_property
    def version(self):
        return self.metadata["kango_version"]


class Scriptify(Framework):
    NAME = "Scriptify"
    METADATA_FILE = "scriptify.json"

    def detect(self):
        return isinstance(self.metadata, dict)

    FRAMEWORK_FILES = ("bootstrap.js",
                       "scriptify.json")

    @cached_property
    def version(self):
        return self.metadata.get("scriptify-version")
