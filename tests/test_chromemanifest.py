import unittest
import os

from validator.chromemanifest import ChromeManifest

def test_open():
    "Open a chrome file and ensure that data can be pulled from it."

    chrome = open("tests/resources/chromemanifest/chrome.manifest")
    chrome_data = chrome.read()

    manifest = ChromeManifest(chrome_data)
    assert manifest is not None
    
    assert manifest.get_value("locale", "basta")["object"] == "resource"
    
    g_obj = list(manifest.get_objects("subject", "predicate"))
    
    assert len(g_obj) == 1
    assert g_obj[0] == "object"
    
    obj_resource = list(manifest.get_triples(None, None, "resource"))
    assert len(obj_resource) == 2
    
    pred_pred = list(manifest.get_triples(None, "predicate", None))
    assert len(pred_pred) == 2
    
    sub_locale = list(manifest.get_triples("locale", None, None))
    assert len(sub_locale) == 2
