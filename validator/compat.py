from validator.decorator import version_range
from validator.constants import (FIREFOX_GUID, FENNEC_GUID,
                                 THUNDERBIRD_GUID as TB_GUID, ANDROID_GUID)


# Compatibility app/version ranges:

def _build_definition(maj_version_num, firefox=True, fennec=True,
                      thunderbird=True, android=True):
    definition = {}
    app_version_range = (
        lambda app: version_range(app, '%d.0a1' % maj_version_num,
                                       '%d.0a1' % (maj_version_num + 1)))
    if firefox:
        definition[FIREFOX_GUID] = app_version_range('firefox')
    if fennec:
        definition[FENNEC_GUID] = app_version_range('fennec')
    if thunderbird:
        definition[TB_GUID] = app_version_range('thunderbird')
    if android:
        definition[ANDROID_GUID] = app_version_range('android')

    return definition


FX45_DEFINITION = _build_definition(45, fennec=False, android=False, thunderbird=False)
FX46_DEFINITION = _build_definition(46, fennec=False, android=False, thunderbird=False)
FX47_DEFINITION = _build_definition(47, fennec=False, android=False, thunderbird=False)
FX48_DEFINITION = _build_definition(48, fennec=False, android=False, thunderbird=False)
FX50_DEFINITION = _build_definition(50, fennec=False, android=False, thunderbird=False)
FX51_DEFINITION = _build_definition(51, fennec=False, android=False, thunderbird=False)
FX52_DEFINITION = _build_definition(52, fennec=False, android=False, thunderbird=False)
FX53_DEFINITION = _build_definition(53, fennec=False, android=False, thunderbird=False)
FX54_DEFINITION = _build_definition(54, fennec=False, android=False, thunderbird=False)
