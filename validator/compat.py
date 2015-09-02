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


FX38_DEFINITION = _build_definition(38)
FX39_DEFINITION = _build_definition(39)
FX40_DEFINITION = _build_definition(40)
FX41_DEFINITION = _build_definition(41)

_tb_definition = (lambda ver:
    _build_definition(ver, firefox=False, fennec=False, android=False))

TB29_DEFINITION = _tb_definition(29)
TB30_DEFINITION = _tb_definition(30)
TB31_DEFINITION = _tb_definition(31)
