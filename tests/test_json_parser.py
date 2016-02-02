import json

from validator.constants import FIREFOX_GUID
from validator.json_parser import ManifestJsonParser


manifest_json = """{
        "name": "My Awesome Addon",
        "version": "1.25",

        "applications": {
            "gecko": {
                "id": "my@awesome.addon"
            }
        }
    }"""

manifest_json_with_versions = """{
        "name": "My Awesome Addon",
        "version": "1.25",

        "applications": {
            "gecko": {
                "id": "my@awesome.addon",
                "strict_min_version": "43.0",
                "strict_max_version": "50.*"
            }
        }
    }"""


def test_parser():
    parser = ManifestJsonParser(None, manifest_json)
    assert parser.data == json.loads(manifest_json)


def test_parser_no_applications():
    parser = ManifestJsonParser(None, """{"name": "foo"}""")
    assert parser.get_applications() == []


def test_get_applications():
    parser = ManifestJsonParser(None, manifest_json)
    assert parser.get_applications() == [{u'guid': FIREFOX_GUID,
                                          u'min_version': u'42.0',
                                          u'max_version': u'*'}]


def test_get_applications_with_versions():
    parser = ManifestJsonParser(None, manifest_json_with_versions)
    assert parser.get_applications() == [{u'guid': FIREFOX_GUID,
                                          u'min_version': u'43.0',
                                          u'max_version': u'50.*'}]
