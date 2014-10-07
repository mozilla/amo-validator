from validator.decorator import version_range
from validator.constants import (FIREFOX_GUID, FENNEC_GUID,
                                 THUNDERBIRD_GUID as TB_GUID, ANDROID_GUID)


# Compatibility app/version ranges:
FX4_DEFINITION = {FIREFOX_GUID: version_range("firefox", "3.7a1pre", "5.0a2"),
                  FENNEC_GUID: version_range("fennec", "4.0b1pre", "5.0a2")}
FX5_DEFINITION = {FIREFOX_GUID: version_range("firefox", "5.0a2", "6.0a1"),
                  FENNEC_GUID: version_range("fennec", "5.0a2", "6.0a1")}

def _build_definition(maj_version_num, firefox=True, fennec=True,
                      thunderbird=True, android=True):
    definition = {}
    app_version_range = (
        lambda app: version_range(app, "%d.0a1" % maj_version_num,
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


FX6_DEFINITION = _build_definition(6, thunderbird=False, android=False)
FX7_DEFINITION = _build_definition(7, android=False)
FX8_DEFINITION = _build_definition(8, android=False)
FX9_DEFINITION = _build_definition(9, android=False)
FX10_DEFINITION = _build_definition(10)
FX11_DEFINITION = _build_definition(11)
FX12_DEFINITION = _build_definition(12)
FX13_DEFINITION = _build_definition(13)
FX14_DEFINITION = _build_definition(14)
FX15_DEFINITION = _build_definition(15)
FX16_DEFINITION = _build_definition(16)
FX17_DEFINITION = _build_definition(17)
FX18_DEFINITION = _build_definition(18)
FX19_DEFINITION = _build_definition(19)
FX20_DEFINITION = _build_definition(20)
FX21_DEFINITION = _build_definition(21)
FX22_DEFINITION = _build_definition(22)
FX23_DEFINITION = _build_definition(23)
FX24_DEFINITION = _build_definition(24)
FX25_DEFINITION = _build_definition(25)
FX26_DEFINITION = _build_definition(26)
FX27_DEFINITION = _build_definition(27)
FX28_DEFINITION = _build_definition(28)
FX29_DEFINITION = _build_definition(29)
FX30_DEFINITION = _build_definition(30)
FX31_DEFINITION = _build_definition(31)
FX32_DEFINITION = _build_definition(32)
FX33_DEFINITION = _build_definition(33)
FX34_DEFINITION = _build_definition(34)
FX35_DEFINITION = _build_definition(35)
FX36_DEFINITION = _build_definition(36)
FX37_DEFINITION = _build_definition(37)
FX38_DEFINITION = _build_definition(38)
FX39_DEFINITION = _build_definition(39)
FX40_DEFINITION = _build_definition(40)

_tb_definition = (lambda ver:
    _build_definition(ver, firefox=False, fennec=False, android=False))

TB6_DEFINITION = {TB_GUID: version_range("thunderbird", "6.0a1", "7.0a1")}
TB7_DEFINITION = {TB_GUID: version_range("thunderbird", "7.0a1", "8.0a1")}
TB8_DEFINITION = {TB_GUID: version_range("thunderbird", "8.0a1", "9.0a1")}
TB9_DEFINITION = {TB_GUID: version_range("thunderbird", "9.0a1", "10.0a1")}
TB10_DEFINITION = {TB_GUID: version_range("thunderbird", "10.0a1", "11.0a1")}
TB11_DEFINITION = {TB_GUID: version_range("thunderbird", "11.0a1", "12.0a1")}
TB12_DEFINITION = {TB_GUID: version_range("thunderbird", "12.0a1", "13.0a1")}
TB13_DEFINITION = _tb_definition(13)
TB14_DEFINITION = _tb_definition(14)
TB15_DEFINITION = _tb_definition(15)
TB16_DEFINITION = _tb_definition(16)
TB17_DEFINITION = _tb_definition(17)
TB18_DEFINITION = _tb_definition(18)
TB19_DEFINITION = _tb_definition(19)
TB20_DEFINITION = _tb_definition(20)
TB21_DEFINITION = _tb_definition(21)
TB22_DEFINITION = _tb_definition(22)
TB23_DEFINITION = _tb_definition(23)
TB24_DEFINITION = _tb_definition(24)
TB25_DEFINITION = _tb_definition(25)
TB26_DEFINITION = _tb_definition(26)
TB27_DEFINITION = _tb_definition(27)
TB28_DEFINITION = _tb_definition(28)
TB29_DEFINITION = _tb_definition(29)
TB30_DEFINITION = _tb_definition(30)
TB31_DEFINITION = _tb_definition(31)
