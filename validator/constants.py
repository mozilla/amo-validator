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

# Defaults the the `brew install spidermonkey` default install location.
# The full path to the Spidermonkey shell.
SPIDERMONKEY_INSTALLATION = "/usr/bin/local/js"

if not os.path.exists(SPIDERMONKEY_INSTALLATION):
    # If that path doesn't exist, try just `js`; it could be in $PATH.
    SPIDERMONKEY_INSTALLATION = "js"

    # It's not in the path that Python is looking for, so explore some more.
    # Graciously provided by @kumar in bug 614574
    if not os.path.exists(SPIDERMONKEY_INSTALLATION):
        found = False
        for p in os.environ.get('PATH', '').split(':'):
            if os.path.exists(os.path.join(p, SPIDERMONKEY_INSTALLATION)):
                found = True
                break

        if not found:
            # The fallback is simply to disable JS tests.
            SPIDERMONKEY_INSTALLATION = None

