from fnmatch import fnmatch as fnm

from validator.constants import (FF4_MIN, FIREFOX_GUID, FENNEC_GUID,
                                 THUNDERBIRD_GUID as TB_GUID, ANDROID_GUID,
                                 PACKAGE_DICTIONARY, )
import validator.decorator as decorator
from validator.decorator import version_range

# Detect blacklisted files based on their extension.
blacklisted_extensions = ('dll', 'exe', 'dylib', 'so',
                          'sh', 'class', 'swf')

blacklisted_magic_numbers = (
        (0x4d, 0x5a),  # EXE/DLL
        (0x5a, 0x4d),  # Alternative for EXE/DLL
        (0x7f, 0x45, 0x4c, 0x46),  # UNIX elf
        (0x23, 0x21),  # Shebang (shell script)
        (0xca, 0xfe, 0xba, 0xbe),  # Java + Mach-O (dylib)
        (0xca, 0xfe, 0xd0, 0x0d),  # Java (packed)
        (0xfe, 0xed, 0xfa, 0xce),  # Mach-O
        (0x46, 0x57, 0x53),  # Uncompressed SWF
        (0x43, 0x57, 0x53),  # ZLIB compressed SWF
)

# If there are more than 10 .class files in a package, it is flagged as a Java
# archive file.
JAVA_JAR_THRESHOLD = 10


def test_unknown_file(err, filename):
    'Tests some sketchy files that require silly code.'

    # Extract the file path and the name from the filename
    path = filename.split('/')
    name = path.pop()

    if name == 'chromelist.txt':
        err.notice(('testcases_packagelayout',
                    'test_unknown_file',
                    'deprecated_file'),
                   'Extension contains a deprecated file',
                   "The file \"%s\" is no longer supported by any modern "
                   'Mozilla product.' % filename,
                   filename)
        return True


@decorator.register_test(tier=1)
def test_blacklisted_files(err, xpi_package=None):
    'Detects blacklisted files and extensions.'

    flagged_files = []

    HELP = ('Please try to avoid interacting with or bundling '
            'native binaries whenever possible. If you are '
            'bundling binaries for performance reasons, please '
            'consider alternatives such as Emscripten '
            '(http://mzl.la/1KrSUh2), JavaScript typed arrays '
            '(http://mzl.la/1Iw02sr), and Worker threads '
            '(http://mzl.la/1OGfAcc).',
            'Any code which bundles native binaries must '
            'submit full source code, and undergo manual code review '
            'for at least one submission.')

    for name in xpi_package:
        file_ = xpi_package.info(name)
        # Simple test to ensure that the extension isn't blacklisted
        extension = file_['extension']
        if extension in blacklisted_extensions:
            # Note that there is a binary extension in the metadata
            err.metadata['contains_binary_extension'] = True
            flagged_files.append(name)
            continue

        # Perform a deep inspection to detect magic numbers for known binary
        # and executable file types.
        zip = xpi_package.zf.open(name)
        bytes = tuple([ord(x) for x in zip.read(4)])  # Longest is 4 bytes
        if [x for x in blacklisted_magic_numbers if bytes[0:len(x)] == x]:
            # Note that there is binary content in the metadata
            err.metadata['contains_binary_content'] = True
            err.warning(
                err_id=('testcases_packagelayout', 'test_blacklisted_files',
                        'disallowed_file_type'),
                warning='Flagged file type found',
                description='A file was found to contain flagged content '
                            '(i.e.: executable data, potentially '
                            'unauthorized scripts, etc.).',
                editors_only=True,
                signing_help=HELP,
                signing_severity='high',
                filename=name)

    if flagged_files:
        # Detect Java JAR files:
        if (sum(1 for f in flagged_files if f.endswith('.class')) >
                JAVA_JAR_THRESHOLD):
            err.warning(
                err_id=('testcases_packagelayout', 'test_blacklisted_files',
                        'java_jar'),
                warning='Java JAR file detected.',
                description='A Java JAR file was detected in the add-on.',
                filename=xpi_package.filename,
                signing_help=HELP,
                signing_severity='high')
        else:
            err.warning(
                err_id=('testcases_packagelayout',
                        'test_blacklisted_files',
                        'disallowed_extension'),
                warning='Flagged file extensions found.',
                description=('Files whose names end with flagged extensions '
                             'have been found in the add-on.',
                             'The extension of these files are flagged '
                             'because they usually identify binary '
                             'components. Please see '
                             'http://addons.mozilla.org/developers/docs/'
                             'policies/reviews#section-binary'
                             ' for more information on the binary content '
                             'review process.',
                             '\n'.join(flagged_files)),
                editors_only=True,
                signing_help=HELP,
                signing_severity='medium',
                filename=name)


@decorator.register_test(tier=1)
def test_godlikea(err, xpi_package):
    """Test to make sure that the godlikea namespace is not in use."""

    if 'chrome/godlikea.jar' in xpi_package:
        err.error(
            err_id=('testcases_packagelayout',
                    'test_godlikea'),
            error="Banned 'godlikea' chrome namespace",
            description="The 'godlikea' chrome namepsace is generated from a "
                        'template and should be replaced with something '
                        'unique to your add-on to avoid name conflicts.',
            filename='chrome/godlikea.jar')


@decorator.register_test(
        tier=5,
        versions={FIREFOX_GUID: version_range('firefox', FF4_MIN),
                  TB_GUID: version_range('thunderbird', '3.3a4pre'),
                  FENNEC_GUID: version_range('fennec', '4.0'),
                  ANDROID_GUID: version_range('android', '11.0a1')})
def test_compatibility_binary(err, xpi_package):
    """
    Flags only binary content as being incompatible with future app releases.
    """

    description = ('Add-ons with binary components must have their '
                   'compatibility manually adjusted. Please test your add-on '
                   'against the new version before updating your maxVersion.')

    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return

    for triple in chrome.triples:
        if triple['subject'] == 'binary-component':
            err.metadata['binary_components'] = True
            err.notice(
                err_id=('testcases_packagelayout',
                        'test_compatibility_binary',
                        'disallowed_file_type'),
                notice='Flagged file type found',
                description=('A file (%s) was registered as a binary '
                             'component. Binary files may not be submitted to '
                             'AMO unless accompanied by source code.'
                                % triple['predicate'],
                             description),
                filename=triple['predicate'],
                compatibility_type='error')


@decorator.register_test(tier=1)
def test_layout_all(err, xpi_package):
    'Tests the well-formedness of extensions.'

    # Subpackages don't need to be tested for install.rdf.
    if xpi_package.subpackage:
        return

    if (not err.get_resource('has_install_rdf') and
            not err.get_resource('bad_install_rdf') and
            not err.get_resource('has_package_json')):
        err.error(('testcases_packagelayout',
                  'test_layout_all',
                  'missing_install_rdf'),
                  'Add-on missing install.rdf.',
                  'All add-ons require an install.rdf file.')
        return

    package_namelist = list(xpi_package.zf.namelist())
    package_nameset = set(package_namelist)
    if len(package_namelist) != len(package_nameset):
        err.error(
            err_id=('testcases_packagelayout', 'test_layout_all',
                    'duplicate_entries'),
            error='Package contains duplicate entries',
            description='The package contains multiple entries with the same '
                        'name. This practice has been banned. Try unzipping '
                        'and re-zipping your add-on package and try again.')


# This test needs to happen in tier 2. install.rdf analysis happens in tier
# 1, which may cause this to generate false positives if it's also on tier 1
# (bug 631340)
@decorator.register_test(tier=2)
def test_emunpack(err, xpi_package):

    if err.get_resource('em:unpack') != 'true':
        # Covers bug 597255

        # Dictionaries should always be unpacked
        fails = err.detected_type == PACKAGE_DICTIONARY
        if not fails:
            executables = ('exe', 'dll', 'so', 'dylib', 'exe', 'bin')
            # Search for unpack-worthy files
            for file_ in xpi_package:
                if file_.startswith('chrome/icons/default/'):
                    fails = True
                    break
                # Executables in /components/ should also be flagged.
                if (file_.startswith('components/') and
                    [x for x in executables if
                     file_[-len(x) - 1:] == '.%s' % x]):
                    fails = True
                    break

        if fails:
            err.warning(('testcases_packagelayout',
                         'test_emunpack',
                         'should_be_true'),
                        'Add-on should set <em:unpack> to true',
                        'The add-on meets criteria indicating that it will '
                        'not work correctly in Gecko 4 and above. Set '
                        "<em:unpack> to 'true' in the install.rdf file to fix "
                        'this.',
                        filename='install.rdf',
                        tier=1)
            return

        # Covers bug 551714

        # This only applies to FF4
        if not err.get_resource('ff4'):
            return

        for file_ in xpi_package:
            if file_.endswith('.jar'):
                err.notice(
                    err_id=('packagelayout', 'emunpack', 'should_be_false'),
                    notice='Add-on contains JAR files, no <em:unpack>',
                    description='The add-on contains JAR files and does not '
                                "set <em:unpack> to 'true'. This can result "
                                'in performance issues in add-ons that target '
                                'Gecko 4 and above. You should either no '
                                'longer use JAR files to package your chrome '
                                'files (preferred) or add '
                                '`<em:unpack>true</em:unpack>` to the '
                                'install.rdf.',
                    filename='install.rdf',
                    tier=1)
                return


@decorator.register_test(tier=1, expected_type=3)
def test_dictionary_layout(err, xpi_package=None):
    """Ensures that dictionary packages contain the necessary
    components and that there are no other extraneous files lying
    around."""

    # Define rules for the structure.
    mandatory_files = [
        'install.rdf',
        'dictionaries/*.aff',
        'dictionaries/*.dic']
    whitelisted_files = [
        'install.js',
        'icon.png',
        'icon64.png',
        'dictionaries/*.aff',  # List again because there must >0
        'dictionaries/*.dic',
        'chrome.manifest',
        'chrome/*']
    whitelisted_extensions = ('txt',)

    test_layout(err, xpi_package, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                'dictionary')


@decorator.register_test(tier=1, expected_type=4)
def test_langpack_layout(err, xpi_package=None):
    """Ensures that language packs only contain exactly what they
    need and nothing more. Otherwise, somebody could sneak something
    sneaking into them."""

    # Define rules for the structure.
    mandatory_files = [
        'install.rdf',
        'chrome.manifest']
    whitelisted_files = ['chrome/*.jar']
    whitelisted_extensions = ('manifest', 'rdf', 'jar', 'dtd',
                              'properties', 'xhtml', 'css')

    test_layout(err, xpi_package, mandatory_files,
                whitelisted_files, whitelisted_extensions,
                'language pack')


@decorator.register_test(tier=1, expected_type=2)
def test_theme_layout(err, xpi_package=None):
    """Ensures that themes only contain exactly what they need and
    nothing more. Otherwise, somebody could sneak something sneaking
    into them."""

    # Define rules for the structure.
    mandatory_files = [
        'install.rdf',
        'chrome.manifest']
    whitelisted_files = ['chrome/*.jar']

    test_layout(err, xpi_package, mandatory_files,
                whitelisted_files, None, 'theme')


def test_layout(err, xpi, mandatory, whitelisted,
                white_extensions=None, pack_type='Unknown Addon'):
    """Tests the layout of a package. Pass in the various types of files
    and their levels of requirement and this guy will figure out which
    files should and should not be in the package."""

    # A shortcut to prevent excessive lookups

    for file_ in xpi:

        if file_ == '.DS_Store' or file_.startswith('__MACOSX/'):
            continue

        # Remove the file from the mandatory file list.
        #if file_ in mandatory_files:
        mfile_list = [mf for mf in mandatory if fnm(file_, mf)]
        if mfile_list:
            # Isolate the mandatory file pattern and remove it.
            mfile = mfile_list[0]
            mandatory.remove(mfile)
            continue

        # Test if the file is in the whitelist.
        if any(fnm(file_, wlfile) for wlfile in whitelisted):
            continue

        # Is it a directory?
        if file_.endswith('/'):
            continue

        # Is the file a sketch file?
        if test_unknown_file(err, file_):
            continue

        # Is it a whitelisted file type?
        if white_extensions is None or file_.split('.')[-1] in white_extensions:
            continue

        # Otherwise, report an error.
        err.warning(('testcases_packagelayout',
                     'test_layout',
                     'unknown_file'),
                    'Unknown file found in add-on',
                    ['Files have been detected that are not allowed within '
                     'this type of add-on. Remove the file or use an '
                     'alternative, supported file format instead.',
                     'Detected file: %s' % file_],
                    file_)

    # If there's anything left over, it means there's files missing
    if mandatory:
        err.warning(('testcases_packagelayout',
                     'test_layout',
                     'missing_required'),
                    'Required file missing',
                    ['This add-on is missing required files. Consult the '
                     'documentation for a full list of required files.',
                     "Add-ons of type '%s' require files: %s" %
                          (pack_type, ', '.join(mandatory))])
