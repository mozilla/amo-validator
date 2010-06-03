import unittest
import os

from chromemanifest import ChromeManifest

def test_open():
    "Open a chrome file and ensure that data can be pulled from it."

    chrome = open("tests/resources/chromemanifest/chrome.manifest")
    chrome_data = chrome.read()

    manifest = ChromeManifest(chrome_data)
    assert manifest is not None
    
    assert manifest.get_value("locale", "basta")["object"] == \
        "resource"
    
    g_obj = manifest.get_objects("subject", "predicate")
    
    assert len(g_obj) == 1
    assert g_obj[0] == "object"
