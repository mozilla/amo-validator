from collections import defaultdict
from itertools import chain
import hashlib
import re

import fastchardet

from validator.constants import (DEPRECATED_HARD, DEPRECATED_MAX,
                                 LIBRARY_METADATA)
from validator.version import Version


HASH_RE = re.compile(r'^[0-9a-f]{64}$', re.I)


def build_hashes(metadata):
    """
    Builds the "hashes" dict of a metadata blob based on the contents of the
    "libraries" and "frameworks" data structures. Generally only called by
    external hash update scripts and tests.
    """
    def merge_deprecated(*args):
        return max(a.get("deprecated", 0) for a in args)

    ignore_hashes = checksum("empty", ""),

    # Flatten all hashes for a class of libraries into
    # hash-details tuples.
    def hashes(lib_type):
        for lib, data in metadata[lib_type].iteritems():
            for version, vdata in data.get("versions", {}).iteritems():
                deprecated = False
                if lib_type == "libraries":
                    # Currently, deprecated library versions propagate to
                    # files, deprecated framework versions do not. We may need
                    # greater granularity in the future.
                    deprecated = merge_deprecated(data, vdata)

                for path, hash_ in vdata.get("files", {}).iteritems():
                    yield (hash_,
                           {"deprecated": deprecated,
                            "sources": [[lib, version, path]]})

    result = defaultdict(lambda: {"sources": []})

    # Merge all hashes and details into a single dict,
    # flattening hashes which are identical across multiple
    # framework versions into a single data structure.
    for hash_, data in chain(hashes("frameworks"), hashes("libraries")):
        if hash_ not in ignore_hashes:
            res = result[hash_]
            res["sources"].extend(data["sources"])
            res["deprecated"] = merge_deprecated(res, data)

    for hash_, data in result.iteritems():
        # Clean up keys which have default values.
        for key in ["deprecated"]:
            if not data[key]:
                del data[key]

    return dict(result)


def validate_metadata(data):
    """
    Performs basic sanity checks on the library metadata structure. Raises an
    AssertionError if invalid.
    """

    def check_messages(dict_):
        if "messages" in dict_:
            return (isinstance(dict_["messages"], list) and
                    all(isinstance(msg, basestring)
                        for msg in dict_["messages"]))
        return True

    def check_deprecated(dict_):
        if "deprecated" in dict_:
            return (isinstance(dict_["deprecated"], int) and
                    0 <= dict_["deprecated"] <= DEPRECATED_MAX)
        return True

    for key in "frameworks", "libraries", "hashes":
        assert isinstance(data.get(key), dict), \
            "Missing valid '%s' dictionary" % key

    for key in "frameworks", "libraries":
        for name, framework in data[key].iteritems():
            assert check_messages(framework), "Invalid messages for %s" % name
            assert check_deprecated(framework), \
                "Invalid deprecation level for %s" % name

            if "versions" not in framework:
                continue

            assert isinstance(framework["versions"], dict), \
                "Invalid versions data for %s/%s" % (key, name)

            for ver_number, ver in framework["versions"].iteritems():
                assert (isinstance(ver.get("files"), dict) and
                        check_messages(ver) and
                        check_deprecated(ver) and
                        all(HASH_RE.match(file)
                            for file in ver["files"].itervalues())), \
                    "Invalid data for %s version %s" % (ver_number, ver)

    def check_source(source):
        return (isinstance(source, (list, tuple)) and
                len(source) == 3 and
                all(isinstance(part, basestring)
                    for part in source))

    for hash_, data in data["hashes"].iteritems():
        assert (HASH_RE.match(hash_) and
                isinstance(data, dict) and
                check_messages(data) and
                isinstance(data.get("sources"), list) and
                all(check_source(source) for source in data["sources"])), \
            "Invalid data for hash %s" % hash_


def checksum(path, data):
    """
    Standardizes the contents of a file and returns a sha256 sum of the
    result. May in the future perform additional mangling depending on
    the file's path.
    """

    try:
        # Deal with some common issues:

        # Standardize encoding
        encoding = fastchardet.detect(data)["encoding"]
        if encoding != "unknown":
            # For unknown encoding, assume binary file.
            try:
                data = unicode(data, encoding)
            except UnicodeDecodeError:
                pass

            # Chop off BOM
            data = re.sub('^\ufeff', '', data)

            # Standardize line endings
            data = re.sub(r'(\r\n?|\n)', '\n', data)

            # Chop off leading and trailing whitespace
            data = data.strip()
    except Exception:
        # Try not to derail the validation process for files with
        # unforseen problems. Just return as good a checksum as we
        # can manage.
        import traceback
        traceback.print_exc()

    if isinstance(data, unicode):
        data = data.encode('UTF-8')

    # Generate checksum
    return hashlib.sha256(data).hexdigest()


def identify_files(identities, library=None):
    """
    Determine the most recent known version of a library common to all
    given files.

    If `library` is passed, returns the latest known version of that library
    with this file. Otherwise returns a tuple containing the ID of a matching
    library, and the latest matching version of that library.
    """
    matches = None

    for identity in identities:
        if not identity or "sources" not in identity:
            return None

        libs = defaultdict(set)
        for lib, version, path in identity["sources"]:
            libs[lib].add(version)

        if matches is None:
            matches = libs
        else:
            for lib, versions in libs:
                matches[lib] = matches[lib].intersection(versions)

    def max_version(versions):
        """Return the highest version number in the `versions` iterable."""
        return str(max(map(Version, versions)))

    if library:
        # We're looking for a version of a specific library. Return
        # the latest version of that library if we have a match.
        if matches and library in matches:
            return max_version(matches[library])
    else:
        # We're looking for any match. Pick out the first library
        # that has a match, and return the highest matching version
        # number.
        match = next(((lib, versions)
                      for lib, versions in matches.iteritems()
                      if versions),
                     None)
        if match:
            return match[0], max_version(match[1])


def detect_libraries(err, xpi):
    """
    Scan all files in the XPI to detect libraries, and report the
    appropriate warnings.
    """
    identified = err.metadata.setdefault("identified_files", {})

    for path in xpi:
        if path.endswith("/"):
            continue

        identity = lookup(path, xpi.read(path))
        if identity:
            identified[path] = identity

            messages = identity.get("messages", [])

            deprecated = identity.get("deprecated", False)
            if deprecated:
                report = (err.warning if deprecated < DEPRECATED_HARD
                          else err.error)
                report(
                    err_id=("testcases_libraries",
                            "detect_libraries",
                            "deprecated_js_library"),
                    message="Banned JavaScript Library Detected",
                    description=(["A known and deprecated JavaScript library "
                                  "has been detected."]
                                 + messages),
                    filename=path)

    # Collect set of all libraries and versions used in add-on.
    libs = defaultdict(set)
    for identity in identified.itervalues():
        for lib, version, path in identity["sources"]:
            libs[lib].add(version)

    # Find libraries with messages.
    metadata = LIBRARY_METADATA["libraries"]
    for libname, versions in libs.iteritems():
        if libname in metadata:
            lib = metadata[libname]
            messages = lib.get("messages", [])
            for ver in versions:
                if ver in lib["versions"]:
                    messages.extend(lib["versions"][ver].get("messages", []))

            if messages:
                err.notice(
                    err_id=("testcases_libraries",
                            "detect_libraries",
                            "detected_library_message"),
                    message="JavaScript Library Detected",
                    description=(["This add-on uses the %s library"
                                  % lib.get("name", libname)]
                                 + messages))


def lookup(path, contents):
    """
    Lookup the identity of a given file based on its path and contents.
    """
    return LIBRARY_METADATA["hashes"].get(checksum(path, contents))
