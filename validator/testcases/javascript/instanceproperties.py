import re
import types

import actions
import jstypes
from validator.constants import BUGZILLA_BUG, EVENT_ASSIGNMENT


JS_URL = re.compile("href=[\'\"]javascript:")


def set_innerHTML(new_value, traverser):
    """Tests that values being assigned to innerHTML are not dangerous."""
    return _set_HTML_property('innerHTML', new_value, traverser)


def set_outerHTML(new_value, traverser):
    """Tests that values being assigned to outerHTML are not dangerous."""
    return _set_HTML_property('outerHTML', new_value, traverser)


# TODO(valcom): Make this generic and put it in utils
def _set_HTML_property(function, new_value, traverser):
    if not isinstance(new_value, jstypes.JSWrapper):
        new_value = jstypes.JSWrapper(new_value, traverser=traverser)

    if new_value.is_literal():
        literal_value = new_value.get_literal_value()
        if isinstance(literal_value, types.StringTypes):
            # Static string assignments

            HELP = ('Please avoid including JavaScript fragments in '
                    'HTML stored in JavaScript strings. Event listeners '
                    'should be added via `addEventListener` after the HTML '
                    'has been injected.',
                    'Injecting <script> nodes should be avoided when at all '
                    'possible. If you cannot avoid loading a script directly '
                    'into a content document, please consider doing so via '
                    'the subscript loader (http://mzl.la/1VGxOPC) instead. '
                    'If the subscript loader is not available, then the '
                    'script nodes should be created using `createElement`, '
                    'and should use a `src` attribute pointing to a '
                    '`resource:` URL within your extension.')

            # Test for on* attributes and script tags.
            if EVENT_ASSIGNMENT.search(literal_value.lower()):
                traverser.warning(
                    err_id=('testcases_javascript_instancetypes',
                            'set_%s' % function, 'event_assignment'),
                    warning='Event handler assignment via %s' % function,
                    description=('When assigning event handlers, %s '
                                 'should never be used. Rather, use a '
                                 'proper technique, like addEventListener.'
                                 % function,
                                 'Event handler code: %s'
                                 % literal_value.encode('ascii', 'replace')),
                    signing_help=HELP,
                    signing_severity='medium')
            elif ('<script' in literal_value or
                  JS_URL.search(literal_value)):
                traverser.warning(
                    err_id=('testcases_javascript_instancetypes',
                            'set_%s' % function, 'script_assignment'),
                    warning='Scripts should not be created with `%s`'
                            % function,
                    description='`%s` should not be used to add scripts to '
                                'pages via script tags or JavaScript URLs. '
                                'Instead, use event listeners and external '
                                'JavaScript.' % function,
                    signing_help=HELP,
                    signing_severity='medium')
            else:
                # Everything checks out, but we still want to pass it through
                # the markup validator. Turn off strict mode so we don't get
                # warnings about malformed HTML.
                from validator.testcases.markup.markuptester import (
                    MarkupParser)
                parser = MarkupParser(traverser.err, strict=False, debug=True)
                parser.process(traverser.filename, literal_value, 'xul')

    else:
        # Variable assignments
        traverser.warning(
            err_id=('testcases_javascript_instancetypes', 'set_%s' % function,
                    'variable_assignment'),
            warning='Markup should not be passed to `%s` dynamically.'
                    % function,
            description='Due to both security and performance concerns, '
                        '%s may not be set using dynamic values which have '
                        'not been adequately sanitized. This can lead to '
                        'security issues or fairly serious performance '
                        'degradation.' % function)


def set_on_event(new_value, traverser):
    """Ensure that on* properties are not assigned string values."""

    is_literal = new_value.is_literal()

    if (is_literal and
            isinstance(new_value.get_literal_value(), types.StringTypes)):
        traverser.warning(
            err_id=('testcases_javascript_instancetypes', 'set_on_event',
                    'on*_str_assignment'),
            warning='on* property being assigned string',
            description='Event handlers in JavaScript should not be '
                        'assigned by setting an on* property to a '
                        'string of JS code. Rather, consider using '
                        'addEventListener.',
            signing_help='Please add event listeners using the '
                         '`addEventListener` API. If the property you are '
                         'assigning to is not an event listener, please '
                         'consider renaming it, if at all possible.',
            signing_severity='medium')
    elif (not is_literal and isinstance(new_value.value, jstypes.JSObject) and
          'handleEvent' in new_value.value.data):
        traverser.warning(
            err_id=('js', 'on*', 'handleEvent'),
            warning='`handleEvent` no longer implemented in Gecko 18.',
            description='As of Gecko 18, objects with `handleEvent` methods '
                        'may no longer be assigned to `on*` properties. Doing '
                        'so will be equivalent to assigning `null` to the '
                        'property.')


def set__proto__(new_value, traverser):
    traverser.warning(
        err_id=('testcases_javascript_instanceproperties', '__proto__'),
        warning='Using __proto__ or setPrototypeOf to set a prototype is now '
                'deprecated.',
        description='Use of __proto__ or setPrototypeOf to set a prototype '
                    'causes severe performance degredation, and is '
                    'deprecated. You should use Object.create instead. '
                    'See bug %s for more information.' % BUGZILLA_BUG % 948227)


def set__exposedProps__(new_value, traverser):
    traverser.warning(
        err_id=('testcases_javascript_instanceproperties', '__exposedProps__'),
        warning='Use of deprecated __exposedProps__ declaration',
        description=(
            'The use of __exposedProps__ to expose objects to unprivileged '
            'scopes is dangerous, and has been deprecated. If objects '
            'must be exposed to unprivileged scopes, `cloneInto` or '
            '`exportFunction` should be used instead.'),
        signing_help='If you are using this API to expose APIs to content, '
                     'please use `Components.utils.cloneInto`, or '
                     '`Components.utils.exportFunction` '
                     '(http://mzl.la/1fvvgm9). If you are using it '
                     'for other purposes, please consider using a built-in '
                     'message passing interface instead. Extensions which '
                     'expose APIs to content will be required to go through '
                     'manual code review for at least one submission.',
        signing_severity='high')


def set_contentScript(value, traverser):
    """Warns when values are assigned to the `contentScript` properties,
    which are essentially the same as calling `eval`."""

    if value.is_literal():
        content_script = actions._get_as_str(value)

        # Avoid import loop.
        from validator.testcases.scripting import test_js_file
        test_js_file(
            traverser.err, traverser.filename, content_script,
            line=traverser.line, context=traverser.context)
    else:
        traverser.warning(
            err_id=('testcases_javascript_instanceproperties',
                    'contentScript', 'set_non_literal'),
            warning='`contentScript` properties should not be used',
            description='Creating content scripts from dynamic values '
                        'is dangerous and error-prone. Please use a separate '
                        'JavaScript file, along with the '
                        '`contentScriptFile` property instead.',
            signing_help='Please do not use the `contentScript` property '
                         'in any add-ons submitted for automated signing.',
            signing_severity='high')


OBJECT_DEFINITIONS = {
    'innerHTML': {'set': set_innerHTML},
    'outerHTML': {'set': set_outerHTML},
    'contentScript': {'set': set_contentScript},
    '__proto__': {'set': set__proto__},
    '__exposedProps__': {'set': set__exposedProps__},
}


def get_operation(mode, prop):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    if prop in OBJECT_DEFINITIONS and mode in OBJECT_DEFINITIONS[prop]:
        return OBJECT_DEFINITIONS[prop][mode]

    elif mode == 'set' and unicode(prop).startswith('on'):
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event
