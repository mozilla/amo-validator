__version__ = '1.10.65'


class ValidationTimeout(Exception):
    """Validation has timed out.

    May be replaced by the exception type raised by an external timeout
    handler when run in a server environment."""

    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return 'Validation timeout after %d seconds' % self.timeout
