import mock
import sys

from validator.main import main


@mock.patch.object(sys, 'stderr')
def test_main(stderr):
    """Test that `main()` initializes without errors."""
    try:
        main()
    except SystemExit:
        pass
