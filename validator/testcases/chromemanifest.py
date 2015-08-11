from validator import decorator


MANIFEST_URI = 'https://developer.mozilla.org/en/XUL_Tutorial/Manifest_Files'

DANGEROUS_CATEGORIES = ('JavaScript-global-constructor',
                        'JavaScript-global-constructor-prototype-alias',
                        'JavaScript-global-property',
                        'JavaScript-global-privileged-property',
                        'JavaScript-global-static-nameset',
                        'JavaScript-global-dynamic-nameset',
                        'JavaScript-DOM-class',
                        'JavaScript-DOM-interface')

DANGEROUS_CATEGORY_WARNING = {
    'err_id': ('testcases_chromemanifest', 'test_resourcemodules',
               'resource_modules'),
    'warning': 'Potentially dangerous category entry',
    'description': 'Add-ons defining global properties via category '
                   'entries require careful review by an administrative '
                   'reviewer.',
    'signing_help': (
        'Given the potential security risks of exposing APIs to unprivileged '
        'code, extensions which use these APIs must undergo manual code '
        'review for at least one submission. If you are not using these APIs '
        'to interact with content code, please consider alternatives, such as '
        'JavaScript modules (http://mzl.la/1HMH2m9), CommonJS modules '
        '(http://mzl.la/1JBMjuU, http://mzl.la/1OBaE8u), the observer '
        'service (http://mzl.la/1MLqWdJ), or window listeners which install '
        'global properties on privileged windows.'),
    'signing_severity': 'medium',
    'editors_only': True}


@decorator.register_test(tier=2, simple=True)
def test_categories(err):
    """Test for categories in the chrome.manifest file."""

    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return

    for triple in chrome.triples:
        if (triple['subject'] == 'category' and
            (triple['predicate'] in DANGEROUS_CATEGORIES or
             (triple['predicate'] == 'JavaScript' and
              (triple['object'].startswith('global ') or
               triple['object'].startswith('DOM '))))):
            err.warning(filename=triple['filename'],
                        line=triple['line'],
                        context=triple['context'],
                        **DANGEROUS_CATEGORY_WARNING)


@decorator.register_test(tier=2, simple=True)
def test_resourcemodules(err):
    """Flag instances of 'resource modules' in chrome.manifest."""

    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return

    for triple in chrome.triples:
        if (triple['subject'] == 'resource' and
                triple['predicate'].startswith('modules')):
            err.error(
                err_id=('testcases_chromemanifest', 'test_resourcemodules',
                        'resource_modules'),
                error="Resources should not be packages in the 'modules' "
                      'namespace',
                description='There should not be resources in the '
                            'chrome.manifest file that are listed as '
                            "'resource modules'.",
                filename=triple['filename'],
                line=triple['line'],
                context=triple['context'])


@decorator.register_test(tier=3, simple=True)
def test_content_instructions(err):
    """Flag content instructions which are not valid."""

    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return

    banned_namespaces = {
            'godlikea': "The 'godlikea' namespace is generated from a "
                        'template and should be replaced with something '
                        'unique to your add-on to avoid name conflicts.'}

    for triple in chrome.get_triples(subject='content'):
        if not triple['predicate'] or not triple['object']:
            err.warning(
                err_id=('testcases_chromemanifest',
                        'test_content_instructions', 'missing_triplicates'),
                warning='`content` instruction missing information',
                description='All content instructions must have a package '
                            'name and a URI to the files it describes.',
                filename=triple['filename'],
                line=triple['line'],
                context=triple['context'])
            continue

        if triple['predicate'] in banned_namespaces:
            err.error(
                err_id=('testcases_chromemanifest',
                        'test_content_instructions', 'godlikea'),
                error='Banned namespace in chrome.manifest',
                description=banned_namespaces[triple['predicate']],
                filename=triple['filename'],
                line=triple['line'],
                context=triple['context'])
        elif (triple['object'] != '' and
              not triple['object'].split()[0].endswith('/')):
            err.notice(
                err_id=('testcases_chromemanifest',
                        'test_content_instructions', 'trailing'),
                notice='Content instruction URIs must end with trailing slash',
                description='Chrome manifest content instructions must have a '
                            'trailing slash on their URI. For more '
                            'information, see %s.' % MANIFEST_URI,
                filename=triple['filename'],
                line=triple['line'],
                context=triple['context'])
