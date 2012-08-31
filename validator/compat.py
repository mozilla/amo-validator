from validator.decorator import version_range
from validator.constants import (FIREFOX_GUID, FENNEC_GUID,
                                 THUNDERBIRD_GUID as TB_GUID, ANDROID_GUID)


# Compatibility app/version ranges:
FX4_DEFINITION = {FIREFOX_GUID: version_range("firefox", "3.7a1pre", "5.0a2"),
                  FENNEC_GUID: version_range("fennec", "4.0b1pre", "5.0a2")}
FX5_DEFINITION = {FIREFOX_GUID: version_range("firefox", "5.0a2", "6.0a1"),
                  FENNEC_GUID: version_range("fennec", "5.0a2", "6.0a1")}

# Starting with FX6, the version number coalesced, so we can use a simple
# helper to build these out.
def _build_definition(maj_version_num, firefox=True, fennec=True,
                      thunderbird=True, android=False):
    definition = {}
    app_version_range = (lambda app:
                             version_range(app,
                                           "%d.0a1" % maj_version_num,
                                           "%d.0a1" % (maj_version_num + 1)))
    if firefox:
        definition[FIREFOX_GUID] = app_version_range("firefox")
    if fennec:
        definition[FENNEC_GUID] = app_version_range("fennec")
    if thunderbird:
        definition[TB_GUID] = app_version_range("thunderbird")
    if android:
        definition[ANDROID_GUID] = app_version_range("android")

    return definition


FX6_DEFINITION = _build_definition(6, thunderbird=False)
FX7_DEFINITION = _build_definition(7)
FX8_DEFINITION = _build_definition(8)
FX9_DEFINITION = _build_definition(9)
FX10_DEFINITION = _build_definition(10, android=True)
FX11_DEFINITION = _build_definition(11, android=True)
FX12_DEFINITION = _build_definition(12, android=True)
FX13_DEFINITION = _build_definition(13, android=True)
FX14_DEFINITION = _build_definition(14, android=True)
FX15_DEFINITION = _build_definition(15, android=True)
FX16_DEFINITION = _build_definition(16, android=True)
FX17_DEFINITION = _build_definition(17, android=True)
FX18_DEFINITION = _build_definition(18, android=True)

TB6_DEFINITION = {TB_GUID: version_range("thunderbird", "6.0a1", "7.0a1")}
TB7_DEFINITION = {TB_GUID: version_range("thunderbird", "7.0a1", "8.0a1")}
TB8_DEFINITION = {TB_GUID: version_range("thunderbird", "8.0a1", "9.0a1")}
TB9_DEFINITION = {TB_GUID: version_range("thunderbird", "9.0a1", "10.0a1")}
TB10_DEFINITION = {TB_GUID: version_range("thunderbird", "10.0a1", "11.0a1")}
TB11_DEFINITION = {TB_GUID: version_range("thunderbird", "11.0a1", "12.0a1")}
TB12_DEFINITION = {TB_GUID: version_range("thunderbird", "12.0a1", "13.0a1")}
TB13_DEFINITION = _build_definition(13, firefox=False, fennec=False)
TB14_DEFINITION = _build_definition(14, firefox=False, fennec=False)
TB15_DEFINITION = _build_definition(15, firefox=False, fennec=False)

