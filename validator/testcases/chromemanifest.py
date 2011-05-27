from validator import decorator
from validator.chromemanifest import ChromeManifest


@decorator.register_test(tier=2, simple=True)
def test_categories(err):
    """Test for categories in the chrome.manifest file."""

    chrome = err.get_resource("chrome.manifest")
    if not chrome:
        return

    for triple in chrome.triples:

        if (triple["subject"] == "category" and
            (triple["predicate"] in
                ("JavaScript-global-constructor",
                 "JavaScript-global-constructor-prototype-alias",
                 "JavaScript-global-property",
                 "JavaScript-global-privileged-property",
                 "JavaScript-global-static-nameset",
                 "JavaScript-global-dynamic-nameset",
                 "JavaScript-DOM-class",
                 "JavaScript-DOM-interface") or
             (triple["predicate"] == "JavaScript" and
              (triple["object"].startswith("global ") or
               triple["object"].startswith("DOM "))))):
            err.warning(("testcases_chromemanifest",
                         "test_categories",
                         "js_categories"),
                        "Add-on should not add JavaScript categories",
                        "Add-ons should not specify categories which define "
                        "properties on JavaScript globals.",
                        filename="chrome.manifest",
                        line=triple["line"],
                        context=chrome.context)


@decorator.register_test(tier=2, simple=True)
def test_resourcemodules(err):
    """Flag instances of 'resource modules' in chrome.manifest."""

    chrome = err.get_resource("chrome.manifest")
    if not chrome:
        return

    for triple in chrome.triples:
        if (triple["subject"] == "resource" and
            triple["predicate"].startswith("modules")):
            err.error(
                err_id=("testcases_chromemanifest", "test_resourcemodules",
                        "resource_modules"),
                error="Resources should not be packages in the 'modules' "
                      "namespace",
                description="There should not be resources in the "
                            "chrome.manifest file that are listed as "
                            "'resource modules'.",
                filename="chrome.manifest",
                line=triple["line"],
                context=chrome.context)


@decorator.register_test(tier=2, simple=True)
def test_banned_content_namespaces(err):
    """Flag content namespaces which have been banned."""

    chrome = err.get_resource("chrome.manifest")
    if not chrome:
        return

    banned_namespaces = {"godlikea":
                             "The 'godlikea' namespace is generated from a "
                             "template and should be replaced with something "
                             "unique to your add-on to avoid name conflicts."}

    for triple in chrome.triples:
        if (triple["subject"] == "content" and
            triple["predicate"] in banned_namespaces):

            err.error(
                err_id=("testcases_chromemanifest",
                        "test_banned_content_namespaces"),
                error="Banned namespace in chrome.manifest",
                description=banned_namespaces[triple["predicate"]],
                filename="chrome.manifest",
                line=triple["line"],
                context=chrome.context)

