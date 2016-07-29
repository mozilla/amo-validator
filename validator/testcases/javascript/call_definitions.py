import math
import re

import actions
import predefinedentities
from jstypes import JSArray, JSObject, JSWrapper

from validator.constants import BUGZILLA_BUG
from validator.compat import FX48_DEFINITION

# Function prototypes should implement the following:
#  wrapper : The JSWrapper instace that is being called
#  arguments : A list of argument nodes; untraversed
#  traverser : The current traverser object


def webbrowserpersist(wrapper, arguments, traverser):
    """
    Most nsIWebBrowserPersist should no longer be used, in favor of the new
    Downloads.jsm interfaces.
    """
    traverser.err.warning(
        err_id=('testcases_javascript_call_definititions',
                'webbrowserpersist'),
        warning='nsIWebBrowserPersist should no longer be used',
        description=('Most nsIWebBrowserPersist methods have been '
                     'superseded by simpler methods in Downloads.jsm, namely '
                     '`Downloads.fetch` and `Downloads.createDownload`. See '
                     'http://mzl.la/downloads-jsm for more information.'),
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        tier=4)


def webbrowserpersist_saveuri(wrapper, arguments, traverser):
    """
    nsIWebBrowserPersist.saveURI requires a valid privacy context as
    of Firefox 19
    """
    if len(arguments) >= 7:
        load_context = traverser._traverse_node(arguments[6])
        if load_context.get_literal_value() is None:
            traverser.err.warning(
                err_id=('testcases_javascript_call_definititions',
                        'webbrowserpersist_saveuri'),
                warning=('saveURI should not be called with a null load '
                         'context'),
                description=('While nsIWebBrowserPersist.saveURI accepts null '
                             'in place of a privacy context, this usage is '
                             'acceptable only when no appropriate load '
                             'context exists.'),
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context,
                tier=4)

    webbrowserpersist(wrapper, arguments, traverser)


def xpcom_constructor(method, extend=False, mutate=False, pretraversed=False):
    """Returns a function which wraps an XPCOM class instantiation function."""

    def definition(wrapper, arguments, traverser):
        """Wraps an XPCOM class instantiation function."""

        if not arguments:
            return None

        traverser._debug('(XPCOM Encountered)')

        if not pretraversed:
            arguments = [traverser._traverse_node(x) for x in arguments]
        argz = arguments[0]

        if not argz.is_global or 'xpcom_map' not in argz.value:
            argz = JSWrapper(traverser=traverser)
            argz.value = {'xpcom_map': lambda: {'value': {}}}

        traverser._debug('(Building XPCOM...)')

        inst = traverser._build_global(
            method, argz.value['xpcom_map']())
        inst.value['overwritable'] = True

        if extend or mutate:
            # FIXME: There should be a way to get this without
            # traversing the call chain twice.
            parent = actions.trace_member(traverser, wrapper['callee']['object'])

            if mutate and not (parent.is_global and
                               isinstance(parent.value, dict) and
                               'value' in parent.value):
                # Assume that the parent object is a first class
                # wrapped native
                parent.value = inst.value

                # FIXME: Only objects marked as global are processed
                # as XPCOM instances
                parent.is_global = True

            if isinstance(parent.value, dict):
                if extend and mutate:
                    if callable(parent.value['value']):
                        parent.value['value'] = \
                            parent.value['value'](t=traverser)

                    parent.value['value'].update(inst.value['value'])
                    return parent

                if extend:
                    inst.value['value'].update(parent.value['value'])

                if mutate:
                    parent.value = inst.value

        return inst
    definition.__name__ = 'xpcom_%s' % str(method)
    return definition


# Global object function definitions:
def string_global(wrapper, arguments, traverser):
    if not arguments:
        return JSWrapper('', traverser=traverser)
    arg = traverser._traverse_node(arguments[0])
    value = actions._get_as_str(arg.get_literal_value())
    return JSWrapper(value, traverser=traverser)


def array_global(wrapper, arguments, traverser):
    output = JSArray()
    if arguments:
        output.elements = [traverser._traverse_node(a) for a in arguments]
    return JSWrapper(output, traverser=traverser)


def number_global(wrapper, arguments, traverser):
    if not arguments:
        return JSWrapper(0, traverser=traverser)
    arg = traverser._traverse_node(arguments[0])
    try:
        value = float(arg.get_literal_value())
    except (ValueError, TypeError):
        return traverser._build_global(
                name='NaN',
                entity=predefinedentities.GLOBAL_ENTITIES[u'NaN'])
    return JSWrapper(value, traverser=traverser)


def boolean_global(wrapper, arguments, traverser):
    if not arguments:
        return JSWrapper(False, traverser=traverser)
    arg = traverser._traverse_node(arguments[0])
    return JSWrapper(bool(arg.get_literal_value()), traverser=traverser)


def python_wrap(func, args, nargs=False):
    """
    This is a helper function that wraps Python functions and exposes them to
    the JS engine. The first parameter should be the Python function to wrap.
    The second parameter should be a list of tuples. Each tuple should
    contain:

     1. The type of value to expect:
        - "string"
        - "num"
     2. A default value.
    """

    def _process_literal(type_, literal):
        if type_ == 'string':
            return actions._get_as_str(literal)
        elif type_ == 'num':
            return actions._get_as_num(literal)
        return literal

    def wrap(wrapper, arguments, traverser):
        passed_args = [traverser._traverse_node(a) for a in arguments]

        params = []
        if not nargs:
            # Handle definite argument lists.
            for type_, def_value in args:
                if passed_args:
                    parg = passed_args[0]
                    passed_args = passed_args[1:]

                    passed_literal = parg.get_literal_value()
                    passed_literal = _process_literal(type_, passed_literal)
                    params.append(passed_literal)
                else:
                    params.append(def_value)
        else:
            # Handle dynamic argument lists.
            for arg in passed_args:
                literal = arg.get_literal_value()
                params.append(_process_literal(args[0], literal))

        traverser._debug('Calling wrapped Python function with: (%s)' %
                             ', '.join(map(str, params)))
        try:
            output = func(*params)
        except (ValueError, TypeError, OverflowError):
            # If we cannot compute output, just return nothing.
            output = None

        return JSWrapper(output, traverser=traverser)

    return wrap


def math_log(wrapper, arguments, traverser):
    """Return a better value than the standard python log function."""
    args = [traverser._traverse_node(a) for a in arguments]
    if not args:
        return JSWrapper(0, traverser=traverser)

    arg = actions._get_as_num(args[0].get_literal_value())
    if arg == 0:
        return JSWrapper(float('-inf'), traverser=traverser)

    if arg < 0:
        return JSWrapper(traverser=traverser)

    arg = math.log(arg)
    return JSWrapper(arg, traverser=traverser)


def math_random(wrapper, arguments, traverser):
    """Return a "random" value for Math.random()."""
    return JSWrapper(0.5, traverser=traverser)


def math_round(wrapper, arguments, traverser):
    """Return a better value than the standard python round function."""
    args = [traverser._traverse_node(a) for a in arguments]
    if not args:
        return JSWrapper(0, traverser=traverser)

    arg = actions._get_as_num(args[0].get_literal_value())
    # Prevent nasty infinity tracebacks.
    if abs(arg) == float('inf'):
        return args[0]

    # Python rounds away from zero, JS rounds "up".
    if arg < 0 and int(arg) != arg:
        arg += 0.0000000000000001
    arg = round(arg)
    return JSWrapper(arg, traverser=traverser)


def nsIJSON_deprec(wrapper, arguments, traverser):
    """Throw a compatibility error about removed XPCOM methods."""
    traverser.notice(
        err_id=('testcases_javascript_calldefinitions', 'nsIJSON',
                'deprec'),
        notice='Deprecated nsIJSON methods in use.',
        description=('The `encode` and `decode` methods in nsIJSON have been '
                     'deprecated in Gecko 7. You can use the methods in the '
                     'global JSON object instead. See %s for more '
                     'information.') %
                         'https://developer.mozilla.org/En/Using_native_JSON')

    return JSWrapper(JSObject(), traverser=traverser, dirty=True)


def js_wrap(wrapper, arguments, traverser):
    """Return the wrapped variant of an unwrapped JSObject."""
    if not arguments:
        traverser._debug('WRAP:NO ARGS')
        return

    traverser._debug('WRAPPING OBJECT')
    obj = traverser._traverse_node(arguments[0])
    if obj.value is None:
        traverser._debug('WRAPPING OBJECT>>NOTHING TO WRAP')
        return JSWrapper(JSObject(), traverser=traverser)

    if len(arguments) > 1:
        traverser.warning(
            err_id=('testcases_js_xpcom', 'xpcnativewrapper', 'shallow'),
            warning='Shallow XPCOM wrappers should not be used',
            description='Shallow XPCOM wrappers are seldom necessary and '
                        'should not be used. Please use deep wrappers '
                        'instead.',
            signing_help='Extensions making use of shallow wrappers will not '
                         'be accepted for automated signing. Please remove '
                         'the second and subsequent arguments of any calls '
                         'to `XPCNativeWrapper`, as well as any code which '
                         'applies `XPCNativeWrapper` to properties obtained '
                         'from these shallowly wrapped objects.',
            signing_severity='high')
        # Do not mark shallow wrappers as not unwrapped.
        return obj

    if obj.is_global:
        # Why are we changing the original object? XPCNativeWrapper
        # does not alter its arguments.
        obj.value['is_unwrapped'] = False
    else:
        obj.value.is_unwrapped = False

    return obj


def js_unwrap(wrapper, arguments, traverser):
    """Return the unwrapped variant of an unwrapped JSObject."""
    if not arguments:
        traverser._debug('UNWRAP:NO ARGS')
        return

    traverser._debug('UNWRAPPING OBJECT')
    obj = traverser._traverse_node(arguments[0])
    if obj.value is None:
        traverser._debug('UNWRAPPING OBJECT>>NOTHING TO UNWRAP')
        return JSWrapper(JSObject(unwrapped=True), traverser=traverser)

    if obj.is_global:
        obj.value['is_unwrapped'] = True
    else:
        obj.value.is_unwrapped = True

    return obj


def open_in_chrome_context(uri, method, traverser):
    if not uri.is_literal():
        traverser.err.notice(
            err_id=('js', 'instanceactions', '%s_nonliteral' % method),
            notice='`%s` called with non-literal parameter.' % method,
            description='Calling `%s` with variable parameters can result in '
                        'potential security vulnerabilities if the variable '
                        'contains a remote URI. Consider using `window.open` '
                        'with the `chrome=no` flag.' % method,
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)

    remote_url = re.compile(r'^(https?|ftp|data):(//)?', re.I)
    uri = unicode(uri.get_literal_value())
    if uri.startswith('//') or remote_url.match(uri):
        traverser.err.warning(
            err_id=('js', 'instanceactions', '%s_remote_uri' % method),
            warning='`%s` called with non-local URI.' % method,
            description='Calling `%s` with a non-local URI will result in the '
                        'dialog being opened with chrome privileges.' % method,
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def Proxy_deprec(wrapper, arguments, traverser):
    traverser.warning(
        err_id=('testcases_javascript_calldefinitions', 'Proxy', 'deprec'),
        warning='Proxy.create and Proxy.createFunction are no longer supported.',
        description=(
            'Proxy.create and Proxy.createFunction are no longer supported. '
            'If this flag appears on Add-ons SDK code, make sure you download '
            'the latest version of the SDK and submit a new version. '
            'See %s for more information.' % BUGZILLA_BUG % 892903),
        compatibility_type='error',
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX48_DEFINITION)
