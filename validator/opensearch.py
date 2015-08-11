from xml.parsers.expat import ExpatError

from defusedxml.minidom import parse
from defusedxml.common import DefusedXmlException

from validator.constants import *


def detect_opensearch(err, package, listed=False):
    'Detect, parse, and validate an OpenSearch provider'

    # Parse the file.
    try:
        # Check if it is a file object.
        if hasattr(package, 'read'):
            srch_prov = parse(package)
        else:
            # It's not a file object; open it (the XML parser is bad at this).
            with open(package, 'rb') as package_file:
                srch_prov = parse(package_file)
    except DefusedXmlException:
        url = 'https://pypi.python.org/pypi/defusedxml/0.3#attack-vectors'
        err.error(
            err_id=('opensearch', 'security_error'),
            error='OpenSearch: XML Security Error',
            description='The OpenSearch extension could not be parsed due to '
                        'a security error in the XML. See {url} for more '
                        'info.'.format(url=url))
        return err
    except ExpatError:
        err.error(
            err_id=('opensearch', 'parse_error'),
            error='OpenSearch: XML Parse Error',
            description='The OpenSearch extension could not be parsed due to '
                        'a syntax error in the XML.')
        return err

    # Make sure that the root element is OpenSearchDescription.
    if srch_prov.documentElement.tagName != 'OpenSearchDescription':
        err.error(
            err_id=('opensearch', 'invalid_document_root'),
            error='OpenSearch: Invalid Document Root',
            description='The root element of the OpenSearch provider is not '
                        "'OpenSearchDescription'.")

    # Per bug 617822
    if not srch_prov.documentElement.hasAttribute('xmlns'):
        err.error(
            err_id=('opensearch', 'no_xmlns'),
            error='OpenSearch: Missing XMLNS attribute',
            description='The XML namespace attribute is missing from the '
                        'OpenSearch document.')

    if ('xmlns' not in srch_prov.documentElement.attributes.keys() or
        srch_prov.documentElement.attributes['xmlns'].value not in (
                    'http://a9.com/-/spec/opensearch/1.0/',
                    'http://a9.com/-/spec/opensearch/1.1/',
                    'http://a9.com/-/spec/opensearchdescription/1.1/',
                    'http://a9.com/-/spec/opensearchdescription/1.0/')):
        err.error(
            err_id=('opensearch', 'invalid_xmlns'),
            error='OpenSearch: Bad XMLNS attribute',
            description='The XML namespace attribute contains an '
                        'value.')

    # Make sure that there is exactly one ShortName.
    sn = srch_prov.documentElement.getElementsByTagName('ShortName')
    if not sn:
        err.error(
            err_id=('opensearch', 'missing_shortname'),
            error='OpenSearch: Missing <ShortName> elements',
            description='ShortName elements are mandatory OpenSearch provider '
                        'elements.')
    elif len(sn) > 1:
        err.error(
            err_id=('opensearch', 'extra_shortnames'),
            error='OpenSearch: Too many <ShortName> elements',
            description='Too many ShortName elements exist in the OpenSearch '
                        'provider.')
    else:
        sn_children = sn[0].childNodes
        short_name = 0
        for node in sn_children:
            if node.nodeType == node.TEXT_NODE:
                short_name += len(node.data)
        if short_name > 16:
            err.error(
                err_id=('opensearch', 'big_shortname'),
                error='OpenSearch: <ShortName> element too long',
                description='The ShortName element must contains less than '
                            'seventeen characters.')

    # Make sure that there is exactly one Description.
    if len(srch_prov.documentElement.getElementsByTagName('Description')) != 1:
        err.error(
            err_id=('opensearch', 'missing_description'),
            error='OpenSearch: Invalid number of <Description> elements',
            description='There are too many or too few Description elements '
                        'in the OpenSearch provider.')

    # Grab the URLs and make sure that there is at least one.
    urls = srch_prov.documentElement.getElementsByTagName('Url')
    if not urls:
        err.error(
            err_id=('opensearch', 'missing_url'),
            error='OpenSearch: Missing <Url> elements',
            description='The OpenSearch provider is missing a Url element.')

    if listed and any(url.hasAttribute('rel') and
                      url.attributes['rel'].value == 'self' for
                      url in urls):
        err.error(
            err_id=('opensearch', 'rel_self'),
            error='OpenSearch: <Url> elements may not be rel=self',
            description='Per AMO guidelines, OpenSearch providers cannot '
                        "contain <Url /> elements with a 'rel' attribute "
                        "pointing to the URL's current location. It must be "
                        'removed before posting this provider to AMO.')

    acceptable_mimes = ('text/html', 'application/xhtml+xml')
    acceptable_urls = [url for url in urls if url.hasAttribute('type') and
                          url.attributes['type'].value in acceptable_mimes]

    # At least one Url must be text/html
    if not acceptable_urls:
        err.error(
            err_id=('opensearch', 'missing_url_texthtml'),
            error="OpenSearch: Missing <Url> element with 'text/html' type",
            description='OpenSearch providers must have at least one Url '
                        "element with a type attribute set to 'text/html'.")

    # Make sure that each Url has the require attributes.
    for url in acceptable_urls:

        if url.hasAttribute('rel') and url.attributes['rel'].value == 'self':
            continue

        if url.hasAttribute('method') and \
           url.attributes['method'].value.upper() not in ('GET', 'POST'):
            err.error(
                err_id=('opensearch', 'missing_method'),
                error="OpenSearch: <Url> element with invalid 'method'",
                description='A Url element in the OpenSearch provider lists a '
                            'method attribute, but the value is not GET or '
                            'POST.')

        # Test for attribute presence.
        if not url.hasAttribute('template'):
            err.error(
                err_id=('opensearch', 'missing_template'),
                error='OpenSearch: <Url> element missing template attribute',
                description='<Url> elements of OpenSearch providers must '
                            'include a template attribute.')
        else:
            url_template = url.attributes['template'].value
            if url_template[:4] != 'http':
                err.error(
                    err_id=('opensearch', 'invalid_template'),
                    error='OpenSearch: `<Url>` element with invalid '
                          '`template`',
                    description='A `<Url>` element in the OpenSearch '
                                'provider lists a template attribute, but '
                                'the value is not a valid HTTP URL.')

            # Make sure that there is a {searchTerms} placeholder in the
            # URL template.
            found_template = url_template.count('{searchTerms}') > 0

            # If we didn't find it in a simple parse of the template=""
            # attribute, look deeper at the <Param /> elements.
            if not found_template:
                for param in url.getElementsByTagName('Param'):
                    # As long as we're in here and dependent on the
                    # attributes, we'd might as well validate them.
                    attribute_keys = param.attributes.keys()
                    if 'name' not in attribute_keys or \
                       'value' not in attribute_keys:
                        err.error(
                            err_id=('opensearch', 'param_missing_attrs'),
                            error='OpenSearch: `<Param>` element missing '
                                  'name/value',
                            description='Param elements in the OpenSearch '
                                        'provider must include a name and a '
                                        'value attribute.')

                    param_value = (param.attributes['value'].value if
                                   'value' in param.attributes.keys() else
                                   '')
                    if param_value.count('{searchTerms}'):
                        found_template = True

                        # Since we're in a validating spirit, continue
                        # looking for more errors and don't break

            # If the template still hasn't been found...
            if not found_template:
                tpl = url.attributes['template'].value
                err.error(
                    err_id=('opensearch', 'template_not_found'),
                    error='OpenSearch: <Url> element missing template '
                          'placeholder',
                    description=('`<Url>` elements of OpenSearch providers '
                                 'must include a template attribute or '
                                 'specify a placeholder with '
                                 '`{searchTerms}`.',
                                 'Missing template: %s' % tpl))

    # Make sure there are no updateURL elements
    if srch_prov.getElementsByTagName('updateURL'):
        err.error(
            err_id=('opensearch', 'banned_updateurl'),
            error='OpenSearch: <updateURL> elements are banned in OpenSearch '
                  'providers.',
            description='OpenSearch providers may not contain <updateURL> '
                        'elements.')

    # The OpenSearch provider is valid!
    return err

