import fnmatch
import re

from validator import decorator
from validator.chromemanifest import ChromeManifest
from validator.contextgenerator import ContextGenerator
from validator.constants import PACKAGE_LANGPACK

BAD_LINK = '(href|src)=["\'](?!chrome:\/\/)(([a-z]*:)?\/\/|data:)'

@decorator.register_test(tier=2, expected_type=PACKAGE_LANGPACK)
def test_langpack_manifest(err, package_contents=None, xpi_package=None):
    """Tests the chrome.manifest files in the package for
    compliance with the standard language pack triples."""
    
    # Don't even both with the test(s) if there's no chrome.manifest.
    if "chrome.manifest" not in package_contents:
        return
    
    # Retrieve the chrome.manifest if it's cached.
    if err.get_resource("chrome.manifest"): # pragma: no cover
        chrome = err.get_resource("chrome.manifest")
    else:
        # Presence is tested by the packagelayout module.
        chrome_data = xpi_package.read("chrome.manifest")
        chrome = ChromeManifest(chrome_data)
        err.save_resource("chrome.manifest", chrome)
    
    for triple in chrome.triples:
        subject = triple["subject"]
        # Test to make sure that the triple's subject is valid
        if subject not in ("locale", "override"):
            err.warning(("testcases_langpack",
                         "test_langpack_manifest",
                         "invalid_subject"),
                        "Invalid chrome.manifest subject",
                        ["""chrome.manifest files in language packs are only
                         allowed to contain items that are prefixed with
                         'locale' or 'override'. Other values are not
                         allowed.""",
                         "Invalid subject: %s" % subject],
                        "chrome.manifest",
                        line=triple["line"],
                        context=chrome.context)
        
        if subject == "override":
            object_ = triple["object"]
            predicate = triple["predicate"]
            
            pattern = "chrome://*/locale/*"
            
            if not fnmatch.fnmatch(object_, pattern) or \
               not fnmatch.fnmatch(predicate, pattern):
                err.warning(("testcases_langpack",
                             "test_langpack_manifest",
                             "invalid_override"),
                            "Invalid chrome.manifest object/predicate.",
                            "'override' entry does not match '%s'" % pattern,
                            "chrome.manifest",
                            line=triple["line"],
                            context=chrome.context)


# This function is called by content.py
def test_unsafe_html(err, filename, data):
    "Tests for unsafe HTML tags in language pack files."
    
    context = ContextGenerator(data)

    unsafe_pttrn = re.compile('<(script|embed|object)', re.I)
    
    match = unsafe_pttrn.search(data)
    if match:
        line = context.get_line(match.start())
        err.warning(("testcases_langpack",
                     "test_unsafe_html",
                     "unsafe_content_html"),
                    "Unsafe HTML found in language pack files.",
                    """Language packs are not allowed to contain scripts,
                    embeds, or other executable code in the language
                    definition files.""",
                    filename,
                    line=line,
                    context=context)
    
    remote_pttrn = re.compile(BAD_LINK, re.I)

    match = remote_pttrn.search(data)
    if match:
        line = context.get_line(match.start())
        err.warning(("testcases_langpack",
                     "test_unsafe_html",
                     "unsafe_content_link"),
                    "Unsafe remote resource found in language pack.",
                    """Language packs are not allowed to contain
                    references to remote resources.""",
                    filename,
                    line=line,
                    context=context)
    

