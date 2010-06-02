import unittest
import os

from chromemanifest import ChromeManifest

def test_open():
    "Open a chrome file and ensure that data can be pulled from it."

    chrome = open("tests/resources/chromemanifest/chrome.manifest")
    chrome_data = chrome.read()

    try:
        manifest = ChromeManifest(chrome_data)
    except:
        assert False
    assert manifest is not None
    
    assert manifest.get_value("locale", "necko")["object"] == \
        "en-ZA jar:chrome/en-ZA.jar!/locale/en-ZA/necko/"
    
    g_obj = manifest.get_objects("locale", "necko")
    
    assert len(g_obj) == 1
    assert g_obj[0] == "en-ZA jar:chrome/en-ZA.jar!/locale/en-ZA/necko/"
