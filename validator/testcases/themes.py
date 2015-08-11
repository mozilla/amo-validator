from validator import decorator
from validator.constants import PACKAGE_THEME


@decorator.register_test(tier=2, expected_type=PACKAGE_THEME)
def test_theme_manifest(err, xpi_package=None):
    """Tests the chrome.manifest files in the package for
    compliance with the standard theme triples."""

    # Don't even both with the test(s) if there's no chrome.manifest.
    chrome = err.get_resource('chrome.manifest')
    if not chrome:
        return

    for triple in chrome.triples:
        subject = triple['subject']
        # Test to make sure that the triple's subject is valid
        if subject not in ('skin', 'style'):
            err.warning(
                err_id=('themes', 'test_theme_manifest',
                        'invalid_chrome_manifest_subject'),
                warning='Invalid chrome.manifest subject',
                description=('chrome.manifest files for full themes are only '
                             "allowed to have 'skin' and 'style' items. "
                             'Other types of items are disallowed for '
                             'security reasons.',
                             'Invalid subject: %s' % subject),
                filename=triple['filename'],
                line=triple['line'],
                context=triple['context'])
