from validator import decorator
from validator.chromemanifest import ChromeManifest
from validator.constants import PACKAGE_THEME


@decorator.register_test(tier=2, expected_type=PACKAGE_THEME)
def test_theme_manifest(err, package_contents=None, xpi_package=None):
    """Tests the chrome.manifest files in the package for
    compliance with the standard theme triples."""

    # Don't even both with the test(s) if there's no chrome.manifest.
    if "chrome.manifest" not in package_contents:
        return None

    # Retrieve the chrome.manifest if it's cached.
    if err.get_resource("chrome.manifest"): # pragma: no cover
        chrome = err.get_resource("chrome.manifest")
    else:
        chrome_data = xpi_package.read("chrome.manifest")
        chrome = ChromeManifest(chrome_data)
        err.save_resource("chrome.manifest", chrome)

    for triple in chrome.triples:
        subject = triple["subject"]
        # Test to make sure that the triple's subject is valid
        if subject not in ("skin",
                           "style"):
            err.warning(("testcases_themes",
                         "test_theme_manifest",
                         "invalid_chrome_manifest_subject"),
                        "Invalid chrome.manifest subject.",
                        ["""chrome.manifest files for themes are only
                         allowed to have 'skin' and 'style' items. Other
                         types of items are disallowed for security
                         reasons.""",
                         "Invalid subject: %s" % subject],
                        "chrome.manifest",
                        line=triple["line"],
                        context=chrome.context)

