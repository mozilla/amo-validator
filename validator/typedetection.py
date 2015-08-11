from validator.constants import *


def detect_type(err, install_rdf=None, xpi_package=None):
    """Determines the type of add-on being validated based on
    install.rdf, file extension, and other properties."""

    # The types in the install.rdf don't pair up 1:1 with the type
    # system that we're using for expectations and the like. This is
    # to help translate between the two.
    translated_types = {'2': PACKAGE_EXTENSION,
                        '4': PACKAGE_THEME,
                        '8': PACKAGE_LANGPACK,
                        '32': PACKAGE_MULTI,
                        '64': PACKAGE_DICTIONARY}

    # If we're missing our install.rdf file, we can try to make some
    # assumptions.
    if install_rdf is None:
        types = {'xpi': PACKAGE_DICTIONARY}

        err.notice(('typedetection',
                    'detect_type',
                    'missing_install_rdf'),
                   'install.rdf was not found.',
                   'The type should be determined by install.rdf if present. '
                   "If it isn't, we still need to know the type.")

        # If we know what the file type might be, return it.
        if xpi_package.extension in types:
            return types[xpi_package.extension]
        # Otherwise, we're out of luck :(
        else:
            return None

    # Attempt to locate the <em:type> node in the RDF doc.
    type_uri = install_rdf.uri('type')
    type_ = install_rdf.get_object(None, type_uri)

    if type_ is not None:
        if type_ in translated_types:
            err.save_resource('is_multipackage', type_ == '32', pushable=True)
            # Make sure we translate back to the normalized version
            return translated_types[type_]
        else:
            err.error(('typedetection',
                       'detect_type',
                       'invalid_em_type'),
                      'Invalid <em:type> value.',
                      'The only valid values for <em:type> are 2, 4, 8, and '
                      '32. Any other values are either invalid or deprecated.',
                      'install.rdf')
            return

    # Dictionaries are weird too, they might not have the obligatory
    # em:type. We can assume that if they have a /dictionaries/ folder,
    # they are a dictionary because even if they aren't, dictionaries
    # have an extraordinarily strict set of rules and file filters that
    # must be passed. It's so crazy secure that it's cool if we use it
    # as kind of a fallback.

    if any(file_ for file_ in xpi_package if
               file_.startswith('dictionaries/')):
        return PACKAGE_DICTIONARY

    if type_ is None:
        err.notice(
            err_id=('typedetection',
                    'detect_type',
                    'no_em:type'),
            notice='No <em:type> element found in install.rdf',
            description="It isn't always required, but it is the most reliable "
                        'method for determining add-on type.',
            filename='install.rdf')

    # There's no type element, so the spec says that it's either a
    # theme or an extension. At this point, we know that it isn't
    # a dictionary, language pack, or multiple extension pack.
    extensions = {'jar': '4',
                  'xpi': '2'}

    # If the package's extension is listed in the [tiny] extension
    # dictionary, then just return that. We'll validate against that
    # add-on type's layout later. Better to false positive than to false
    # negative.
    if xpi_package.extension in extensions:
        # Make sure it gets translated back to the normalized version
        install_rdf_type = extensions[xpi_package.extension]
        return translated_types[install_rdf_type]

