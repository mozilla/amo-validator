import json

from validator import unicodehelper
from validator.constants import FIREFOX_GUID


class ManifestJsonParser(object):
    """Parser wrapper for manifest.json files."""

    def __init__(self, err, data, namespace=None):
        self.err = err
        self.data = json.loads(unicodehelper.decode(data))

    def get_applications(self):
        """Return the list of supported applications."""
        if ('applications' not in self.data or
                'gecko' not in self.data['applications']):
            return []
        app = self.data['applications']['gecko']
        min_version = app.get('strict_min_version', u'42.0')
        max_version = app.get('strict_max_version', u'*')
        return [{u'guid': FIREFOX_GUID,
                 u'min_version': min_version,
                 u'max_version': max_version}]
