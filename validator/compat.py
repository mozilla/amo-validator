from validator.decorator import version_range


# Compatibility app/version ranges:
FX4_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "3.7a1pre", "5.0a2"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "4.0b1pre", "5.0a2")}
FX5_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "5.0a2", "6.0a1"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "5.0a2", "6.0a1")}
FX6_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "6.0a1", "7.0a1"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "6.0a1", "7.0a1")}
FX7_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "7.0a1", "8.0a1"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "7.0a1", "8.0a1"),
                  "{3550f703-e582-4d05-9a08-453d09bdfdc6}":
                      version_range("thunderbird", "7.0a1", "8.0a1")}
FX8_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "8.0a1", "9.0a1"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "8.0a1", "9.0a1"),
                  "{3550f703-e582-4d05-9a08-453d09bdfdc6}":
                      version_range("thunderbird", "8.0a1", "9.0a1")}
FX9_DEFINITION = {"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                      version_range("firefox", "9.0a1", "10.0a1"),
                  "{a23983c0-fd0e-11dc-95ff-0800200c9a66}":
                      version_range("fennec", "9.0a1", "10.0a1"),
                  "{3550f703-e582-4d05-9a08-453d09bdfdc6}":
                      version_range("thunderbird", "9.0a1", "10.0a1")}
TB7_DEFINITION = {"{3550f703-e582-4d05-9a08-453d09bdfdc6}":
                      version_range("thunderbird", "7.0a1", "8.0a1")}
