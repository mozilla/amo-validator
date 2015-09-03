"""Contains generic regular expression tests which run against the entire
contents of files."""
import os
import re

from validator.contextgenerator import ContextGenerator
from .base import RegexTestBase


class FileRegexTest(RegexTestBase):
    """Matches regular expressions in complete file texts, with filters
    for individual tests."""

    TEST_ID = ('testcases_regex', 'raw_file')

    # Extensions of files which are likely to contain JavaScript.
    JAVASCRIPT_EXTENSIONS = ('.js', '.jsm', '.htm', '.html', '.xhtml',
                             '.xul', '.xbl')

    DEFAULT_FILTER = {
        'is_javascript': True,
    }

    def test(self, string, err, filename, context=None):
        extension = os.path.splitext(filename)[1]
        filters = {'filename': filename,
                   'extension': extension,
                   'is_javascript': extension in self.JAVASCRIPT_EXTENSIONS,
                   'document': string}

        # Don't bother running tests unless some of our tests match the file.
        if any(self.check_filter(test, filters)
               for test in self.tests.itervalues()):

            if context is None:
                context = ContextGenerator(string)

            super(FileRegexTest, self).test(string, err=err, filters=filters,
                                            filename=filename, context=context)


def strip_whitespace(val):
    """Removes all white space from the given string or unicode value."""
    return re.sub(r'\s+', '', val)


FILE_REGEXPS = [
    # Access to Sync service modules which don't work well with extensions.
    (r'resource://services-sync',
     {'err_id': ('testcases_regex', 'file', 'sync-service'),
      'warning': 'Sync services objects are not intended to be re-used',
      'description': (
         'The Sync services objects are not intended to be re-used, and '
         'they often change in ways that break add-ons. It is strongly '
         'recommended that you do not rely on them.')}),

    # Use of mouse events with potential performance impacts.
    (r'\bmouse(?:move|over|out)\b',
     {'err_id': ('testcases_regex', 'file', 'mouse-events'),
      'warning': 'Mouse events may cause performance issues.',
      'description': (
         'The use of `mousemove`, `mouseover`, and `mouseout` is '
         'discouraged. These events are dispatched with high frequency '
         'and can cause severe performance issues.')}),

    # Possible attempts to replace the new tab page.
    (strip_whitespace(r"""
        == \s* ["']about:(newtab|blank)["'] |
        ["']about:(newtab|blank)["'] \s* == |
        /\^?about:newtab\$?/ \s* \. test\b |
        \?what=newtab
     """),
     {'err_id': ('testcases_regex', 'file', 'new-tab-page'),
      'warning': 'Possible attempt to override new tab page',

      'description': (
         'The new tab page should be changed only by writing '
         'to the appropriate preference in the default preferences '
         'branch. Such changes may only be made after an explicit '
         'user opt-in, unless the add-on was explicitly and directly '
         'installed by the user, and changing the new tab page is its '
         'primary purpose.',
         'If this code does not change the behavior of the new tab '
         'page, it may be ignored.'),

      'signing_help':
         'Extensions may not programmatically override the new tab '
         'page. If this code has another purpose, we nonetheless '
         'recommend against testing URLs for these values, since '
         'results can be unpredictable, and better options usually '
         'exist. If you cannot avoid making these tests, please leave '
         'this code unchanged, and it will be ignored in future '
         'submissions.',

      'signing_severity': 'low'}),

    # Modification of native object prototypes.
    # This really needs to be a code test, but that's surprisingly difficult
    # to achieve the way things are currently set up.
    (r'\b(?:String|Object|Number|Date|RegExp|Function|Boolean|Array|Iterator)'
     r'\.prototype(?:\.[a-zA-Z_$][a-zA-Z0-9_$]*|\[[^\]]+\])\s*=',

     {'filter': lambda kw: (
         kw['is_javascript'] and not (kw['extension'] == '.jsm' or
                                      'EXPORTED_SYMBOLS' in kw['document'])),

      'err_id': ('testcases_regex', 'file', 'prototype-extension'),
      'warning': 'JavaScript native prototype extension',
      'description': 'Due to interoperability concerns, extensions may '
                     'not extend the prototypes of native objects when '
                     'running in a shared scope.'}),

    # Use of deprecated DOM mutation events.
    (r'\b(?:on)?(?:%s)\b' % '|'.join((
        'DOMAttrModified', 'DOMAttributeNameChanged',
        'DOMCharacterDataModified', 'DOMElementNameChanged',
        'DOMNodeInserted', 'DOMNodeInsertedIntoDocument',
        'DOMNodeRemoved', 'DOMNodeRemovedFromDocument',
        'DOMSubtreeModified')),

     {'err_id': ('testcases_regex', 'file', 'mutation-events'),
      'warning': 'DOM mutation events are deprecated',
      'description': 'DOM mutation events officially deprecated, due '
                     'to their severe performance impact, and should not '
                     'be used. Please use MutationObserver '
                     'objects, or other triggers which do not involve '
                     'directly checking the DOM.'}),
]

# Unsafe template escapes.
FILE_REGEXPS.extend(
    (re.escape(unsafe),
     {'filter': {
         'extension': ('.js', '.jsm', '.hbs', '.handlebars', '.mustache',
                       '.htm', '.html', '.xhtml', '.thtml', '.tmpl', '.tpl')},

      'err_id': ('testcases_regex', 'file', 'unsafe-template-escapes'),
      'warning': 'Potentially unsafe template escape sequence',
      'description': (
          'The use of non-HTML-escaping template escape sequences is '
          'potentially dangerous and highly discouraged. Non-escaped '
          'HTML may only be used when properly sanitized, and in most '
          'cases safer escape sequences such as `{0}` must be used '
          'instead.'.format(safe))})

    for unsafe, safe in (('<%=', '<%-'),
                         ('{{{', '{{'),
                         ('ng-bind-html-unsafe=', 'ng-bind-html'))
)


validate_file = FileRegexTest(FILE_REGEXPS).test
