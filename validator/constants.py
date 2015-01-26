"Constants that will be used across files."

import json
import os
import re
import types


DESCRIPTION_TYPES = types.StringTypes + (list, tuple, )

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_EXTENSION = 1
PACKAGE_THEME = 2
PACKAGE_DICTIONARY = 3
PACKAGE_LANGPACK = 4
PACKAGE_SEARCHPROV = 5
PACKAGE_MULTI = 1  # A multi extension is an extension
PACKAGE_SUBPACKAGE = 7
PACKAGE_WEBAPP = 8

# The "earliest" version number for Firefox 4
FF4_MIN = "3.7a1pre"

# Application GUIDs
FIREFOX_GUID = "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}"
MOZILLA_GUID = "{86c18b42-e466-45a9-ae7a-9b95ba6f5640}"
THUNDERBIRD_GUID = "{3550f703-e582-4d05-9a08-453d09bdfdc6}"
SUNBIRD_GUID = "{718e30fb-e89b-41dd-9da7-e25a45638b28}"
SEAMONKEY_GUID = "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}"
FENNEC_GUID = "{a23983c0-fd0e-11dc-95ff-0800200c9a66}"
ANDROID_GUID = "{aa3c5121-dab2-40e2-81ca-7ea25febc110}"

APPLICATIONS = {
    FIREFOX_GUID: "firefox",
    MOZILLA_GUID: "mozilla",
    THUNDERBIRD_GUID: "thunderbird",
    SUNBIRD_GUID: "sunbird",
    SEAMONKEY_GUID: "seamonkey",
    FENNEC_GUID: "fennec",
    ANDROID_GUID: "android",
}

with open(os.path.join(os.path.dirname(__file__), "app_versions.json")) as avs:
    APPROVED_APPLICATIONS = json.load(avs)

SPIDERMONKEY_INSTALLATION = os.environ.get("SPIDERMONKEY_INSTALLATION")

DEFAULT_WEBAPP_MRKT_URLS = ["https://marketplace.mozilla.org",
                            "https://marketplace-dev.allizom.org"]
BUGZILLA_BUG = "https://bugzil.la/%d"
MDN_DOC = "https://developer.mozilla.org/docs/%s"

JETPACK_URI_URL = "https://wiki.mozilla.org/Labs/Jetpack/Release_Notes/" \
                      "1.4#Known_Issues"

# The maximum size of any string in JS analysis.
MAX_STR_SIZE = 1024 * 24  # 24KB

# The maximum number of JS files that can be exhaustively validated in one
# package.
MAX_JS_THRESHOLD = 900

# The pattern that matches event assignments
# TODO(valcom): Move this to valcom when that's a thing.
EVENT_ASSIGNMENT = re.compile("<.+ on[a-z]+=")

# Graciously provided by @kumar in bug 614574
if (not SPIDERMONKEY_INSTALLATION or
    not os.path.exists(SPIDERMONKEY_INSTALLATION)):
    for p in os.environ.get('PATH', '').split(':'):
        SPIDERMONKEY_INSTALLATION = os.path.join(p, "js")
        if os.path.exists(os.path.join(p, SPIDERMONKEY_INSTALLATION)):
            break

if not os.path.exists(SPIDERMONKEY_INSTALLATION):

    ############ Edit this to change the Spidermonkey location #############
    SPIDERMONKEY_INSTALLATION = "/usr/bin/js"

    if not os.path.exists(SPIDERMONKEY_INSTALLATION):
        # The fallback is simply to disable JS tests.
        SPIDERMONKEY_INSTALLATION = None

try:
    from validator.constants_local import *
except ImportError:
    pass

