import re

VERSION_PATTERN = re.compile('^[-+*.\w]{,32}$')


def validate_name(err, value, source):
    'Tests an install.rdf name value for trademarks.'

    ff_pattern = re.compile('(mozilla|firefox)', re.I)

    err.metadata['name'] = value

    if ff_pattern.search(value):
        err.warning(
            ('metadata_helpers', '_test_name', 'trademark'),
            'Add-on has potentially illegal name.',
            'Add-on names cannot contain the Mozilla or Firefox '
            'trademarks. These names should not be contained in add-on '
            'names if at all possible.',
            source)


def validate_id(err, value, source):
    'Tests an install.rdf UUID value'

    field_name = '<em:id>' if source == 'install.rdf' else 'id'

    id_pattern = re.compile(
        '('
        # UUID format.
        '\{[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}\}'
        '|'
        # "email" format.
        '[a-z0-9-\.\+_]*\@[a-z0-9-\._]+'
        ')',
        re.I)

    err.metadata['id'] = value

    # Must be a valid UUID string.
    if not id_pattern.match(value):
        err.error(
            ('metadata_helpers', '_test_id', 'invalid'),
            'The value of {name} is invalid'.format(name=field_name),
            ['The values supplied for {name} in the {source} file is not a '
             'valid UUID string or email address.'.format(
                 name=field_name, source=source),
             'For help, please consult: '
             'https://developer.mozilla.org/en/install_manifests#id'],
            source)


def validate_version(err, value, source):
    'Tests an install.rdf version number'


    field_name = '<em:version>' if source == 'install.rdf' else 'version'

    err.metadata['version'] = value

    # May not be longer than 32 characters
    if len(value) > 32:
        err.error(
            ('metadata_helpers', '_test_version', 'too_long'),
            'The value of {name} is too long'.format(name=field_name),
            'Values supplied for {name} in the {source} file must be 32 '
            'characters or less.'.format(name=field_name, source=source),
            source)

    # Must be a valid version number.
    if not VERSION_PATTERN.match(value):
        err.error(
            ('metadata_helpers', '_test_version', 'invalid_format'),
            'The value of {name} is invalid'.format(name=field_name),
            'The values supplied for version in the {source} file is not a '
            'valid version string. It can only contain letters, numbers, and '
            'the symbols +*.-_.'.format(name=field_name, source=source),
            source)
