import decorator
from chromemanifest import ChromeManifest


@decorator.register_test(tier=2, expected_type=2)
def test_theme_manifest(err, package_contents=None, xpi_package=None):
    """Tests the chrome.manifest files in the package for
    compliance with the standard theme triples."""

    # Don't even both with the test(s) if there's no chrome.manifest.
    if "chrome.manifest" not in package_contents:
        return

    # Retriece the chrome.manifest if it's cached.
    if err.get_resource("chrome.manifest"):
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
            err.error("Invalid chrome.manifest subject: %s" % subject)