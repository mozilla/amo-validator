import testcases
import testcases.targetapplication
from helper import _do_test


def test_ta_seamonkey():
    """Tests that files that list SeaMonkey support include the
    mandatory install.js file."""
    
    _do_test("tests/resources/targetapplication/bad_seamonkey.xpi",
             testcases.targetapplication.test_targetedapplications,
             True,
             True)