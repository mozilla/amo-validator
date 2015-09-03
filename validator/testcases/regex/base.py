import re

from validator.errorbundler import format_message


class RegexTestBase(object):
    """
    Compiles a list of regular expressions (or iterables of literal strings)
    into a singular regular expression, and emits warnings for each match.
    """

    TEST_ID = ('testcases_regex', 'basic')

    def __init__(self, regexps):
        KEY = 'test_{0}'

        self.tests = {}
        self.patterns = {}
        for i, (regexp, test) in enumerate(regexps):
            key = KEY.format(i)

            test['test_id'] = key
            self.patterns[key] = self.process_key(regexp)
            self.tests[key] = test

        self.regex = re.compile('|'.join(
            r'(?P<{0}>{1})'.format(key, pattern)
            for key, pattern in self.patterns.iteritems()))

    def process_key(self, key):
        """Processes a key into a regular expression. Currently turns an
        enumerable value into a regexp which matches a string which is
        exactly equal to any included value."""

        if isinstance(key, basestring):
            return key

        return r'^(?:{0})$'.format('|'.join(map(re.escape, key)))

    def check_filter(self, test, context):
        """Return true if the given test's filter value matches the given
        context data.

        The filter may be one of:

            * A function which, when called with a context dict, must return
              either True or False.
            * A dict, which matches if, and only if, every key in said dict
              has a matching key and value in `context`.

        Examples:

            * `'filter': {'extension': ('.js', '.json')}`
              Matches files with '.js' or '.json' extensions.

            * `'filter': {'filename': r'/test_.*\.js$',
                          'document': 'TestCase'}`
              Matches JavaScript files which start with 'test_' and contain
              the string 'TestCase'.

            * `'filter': lambda context: (context['extension'] == '.js' or
                                          'ft=js' in context['document'])`
              Matches files which have the `.js` extension or contain the
              string 'ft=js'.
        """

        filter_ = test.get('filter', self.DEFAULT_FILTER)

        if callable(filter_):
            # If we have a function, just call it with our arguments.
            return filter_(context)

        def check_match(matcher, value):
            """Return true if the given matcher matches the given value."""
            # Strings are matched as regular expressions, lists and
            # tuples are matched if any item compares as equal, and
            # anything else is matched on pure equality.

            if isinstance(matcher, basestring):
                return re.search(matcher, value)
            elif isinstance(matcher, (list, tuple)):
                return value in matcher
            else:
                return matcher == value

        # For the given filter dict, if any value does not match the
        # value of the same key in `context`, we fail.
        return all(check_match(matcher, context[key])
                   for key, matcher in filter_.iteritems())

    def test(self, string, filters=None, **kw):
        """Test the given string against each of our patterns, and call
        `report_error` for any matching tests, as long as they aren't excluded
        by `check_filter`."""

        for match in self.regex.finditer(string):
            for key, val in match.groupdict().iteritems():
                if val is not None and key in self.tests:
                    test = self.tests[key]

                    # If we have any filters, make sure the test matches them.
                    if filters and not self.check_filter(test, filters):
                        continue

                    self.report_match(test, match_string=val, match=match,
                                      **kw)

    def report_match(self, test, match_string, match, err, extra=None,
                     filename=None, context=None):
        """Report the match to the error bundle, with appropriate default
        values for:

            * "err_id"
            * "filename" if `filename` is given.
            * "line" and "context" if `context` is given.

        and extra parameters from the `extra` dict, if provided.

        Message strings have the following format keywords available to them:

            * `match` The full text matched by the test's pattern.
        """

        test = test.copy()
        test.setdefault('err_id', self.patterns[test['test_id']])

        # Filters and test IDs should not be passed to the reporter function.
        for key in 'filter', 'test_id':
            if key in test:
                del test[key]

        format_message(test, match=match_string)

        base_message = {'err_id': self.TEST_ID}
        # Add context information if it's available.
        if filename:
            base_message['filename'] = filename
        if context:
            base_message['context'] = context
            base_message['line'] = context.get_line(match.start())

        return err.report(base_message, test, extra)
