import validator.decorator as decorator
from validator.constants import *

@decorator.register_test(tier=5,
                         versions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}":
                                       ["5.0.*"]})
def firefox_5_test(err, package, xpi):
    """Output a test message when Firefox 5 is supported."""
    err.notice(
        err_id=("testcases_compatibility",
                "firefox_5_test",
                "fx5_notice"),
        notice="Firefox 5 Compatibility Detected",
        description="Potential compatibility for FX5 was detected.",
        for_appversions={"{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": ["5.0.*"]})

