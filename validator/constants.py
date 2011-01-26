"Constants that will be used across files."

import os

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_EXTENSION = 1
PACKAGE_THEME = 2
PACKAGE_DICTIONARY = 3
PACKAGE_LANGPACK = 4
PACKAGE_SEARCHPROV = 5
PACKAGE_MULTI = 1 # A multi extension is an extension
PACKAGE_SUBPACKAGE = 7

# The "earliest" version number for Firefox 4
FF4_MIN = "3.7a1pre"

SPIDERMONKEY_INSTALLATION = os.environ.get("SPIDERMONKEY_INSTALLATION")

# Graciously provided by @kumar in bug 614574
if not os.path.exists(SPIDERMONKEY_INSTALLATION):
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

