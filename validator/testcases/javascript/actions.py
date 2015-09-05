from copy import deepcopy
from functools import partial
import sys
import types

# Global import of predefinedentities will cause an import loop
import instanceactions
from validator.constants import (BUGZILLA_BUG, DESCRIPTION_TYPES, FENNEC_GUID,
                                 FIREFOX_GUID, MAX_STR_SIZE)
from validator.decorator import version_range
from jstypes import JSArray, JSContext, JSLiteral, JSObject, JSWrapper


NUMERIC_TYPES = (int, long, float, complex)

# None of these operations (or their augmented assignment counterparts) should
# be performed on non-numeric data. Any time we get non-numeric data for these
# guys, we just return window.NaN.
NUMERIC_OPERATORS = ('-', '*', '/', '%', '<<', '>>', '>>>', '|', '^', '&')
NUMERIC_OPERATORS += tuple('%s=' % op for op in NUMERIC_OPERATORS)


def get_NaN(traverser):
    # If we've cached the traverser's NaN instance, just use that.
    ncache = getattr(traverser, 'NAN_CACHE', None)
    if ncache is not None:
        return ncache

    # Otherwise, we need to import GLOBAL_ENTITIES and build a raw copy.
    from predefinedentities import GLOBAL_ENTITIES
    ncache = traverser._build_global('NaN', GLOBAL_ENTITIES[u'NaN'])
    # Cache it so we don't need to do this again.
    traverser.NAN_CACHE = ncache
    return ncache


def _get_member_exp_property(traverser, node):
    """Return the string value of a member expression's property."""

    if node['property']['type'] == 'Identifier' and not node.get('computed'):
        return unicode(node['property']['name'])
    else:
        eval_exp = traverser._traverse_node(node['property'])
        return _get_as_str(eval_exp.get_literal_value())


def _expand_globals(traverser, node):
    """Expands a global object that has a lambda value."""

    if node.is_global and callable(node.value.get('value')):
        result = node.value['value'](traverser)
        if isinstance(result, dict):
            output = traverser._build_global('--', result)
        elif isinstance(result, JSWrapper):
            output = result
        else:
            output = JSWrapper(result, traverser)

        # Set the node context.
        if 'context' in node.value:
            traverser._debug('CONTEXT>>%s' % node.value['context'])
            output.context = node.value['context']
        else:
            traverser._debug('CONTEXT>>INHERITED')
            output.context = node.context

        return output

    return node


def trace_member(traverser, node, instantiate=False):
    'Traces a MemberExpression and returns the appropriate object'

    traverser._debug('TESTING>>%s' % node['type'])
    if node['type'] == 'MemberExpression':
        # x.y or x[y]
        # x = base
        base = trace_member(traverser, node['object'], instantiate)
        base = _expand_globals(traverser, base)

        identifier = _get_member_exp_property(traverser, node)

        # Handle the various global entity properties.
        if base.is_global:
            # If we've got an XPCOM wildcard, return a copy of the entity.
            if 'xpcom_wildcard' in base.value:
                traverser._debug('MEMBER_EXP>>XPCOM_WILDCARD')

                from predefinedentities import CONTRACT_ENTITIES
                if identifier in CONTRACT_ENTITIES:
                    kw = dict(err_id=('js', 'actions', 'dangerous_contract'),
                              warning='Dangerous XPCOM contract ID')
                    kw.update(CONTRACT_ENTITIES[identifier])

                    traverser.warning(**kw)

                base.value = base.value.copy()
                del base.value['xpcom_wildcard']
                return base

        test_identifier(traverser, identifier)

        traverser._debug('MEMBER_EXP>>PROPERTY: %s' % identifier)
        output = base.get(
            traverser=traverser, instantiate=instantiate, name=identifier)
        output.context = base.context

        if base.is_global:
            # In the cases of XPCOM objects, methods generally
            # remain bound to their parent objects, even when called
            # indirectly.
            output.parent = base
        return output

    elif node['type'] == 'Identifier':
        traverser._debug('MEMBER_EXP>>ROOT:IDENTIFIER')
        test_identifier(traverser, node['name'])

        # If we're supposed to instantiate the object and it doesn't already
        # exist, instantitate the object.
        if instantiate and not traverser._is_defined(node['name']):
            output = JSWrapper(JSObject(), traverser=traverser)
            traverser.contexts[0].set(node['name'], output)
        else:
            output = traverser._seek_variable(node['name'])

        return _expand_globals(traverser, output)
    else:
        traverser._debug('MEMBER_EXP>>ROOT:EXPRESSION')
        # It's an expression, so just try your damndest.
        return traverser._traverse_node(node)


def test_identifier(traverser, name):
    'Tests whether an identifier is banned'

    import predefinedentities
    if name in predefinedentities.BANNED_IDENTIFIERS:
        traverser.err.warning(
            err_id=('js', 'actions', 'banned_identifier'),
            warning='Banned or deprecated JavaScript Identifier',
            description=predefinedentities.BANNED_IDENTIFIERS[name],
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def _function(traverser, node):
    'Prevents code duplication'

    def wrap(traverser, node):
        me = JSObject()

        traverser.function_collection.append([])

        # Replace the current context with a prototypeable JS object.
        traverser._pop_context()
        me.type_ = 'default'  # Treat the function as a normal object.
        traverser._push_context(me)
        traverser._debug('THIS_PUSH')
        traverser.this_stack.append(me)  # Allow references to "this"

        # Declare parameters in the local scope
        params = []
        for param in node['params']:
            if param['type'] == 'Identifier':
                params.append(param['name'])
            elif param['type'] == 'ArrayPattern':
                for element in param['elements']:
                    # Array destructuring in function prototypes? LOL!
                    if element is None or element['type'] != 'Identifier':
                        continue
                    params.append(element['name'])

        local_context = traverser._peek_context(1)
        for param in params:
            var = JSWrapper(lazy=True, traverser=traverser)

            # We can assume that the params are static because we don't care
            # about what calls the function. We want to know whether the
            # function solely returns static values. If so, it is a static
            # function.
            local_context.set(param, var)

        traverser._traverse_node(node['body'])

        # Since we need to manually manage the "this" stack, pop off that
        # context.
        traverser._debug('THIS_POP')
        traverser.this_stack.pop()

        # Call all of the function collection's members to traverse all of the
        # child functions.
        func_coll = traverser.function_collection.pop()
        for func in func_coll:
            func()

    # Put the function off for traversal at the end of the current block scope.
    traverser.function_collection[-1].append(partial(wrap, traverser, node))

    return JSWrapper(traverser=traverser, callable=True, dirty=True)


def _define_function(traverser, node):
    me = _function(traverser, node)
    traverser._peek_context(2).set(node['id']['name'], me)
    return me


def _func_expr(traverser, node):
    'Represents a lambda function'

    return _function(traverser, node)


def _define_with(traverser, node):
    'Handles `with` statements'

    object_ = traverser._traverse_node(node['object'])
    if isinstance(object_, JSWrapper) and isinstance(object_.value, JSObject):
        traverser.contexts[-1] = object_.value
        traverser.contexts.append(JSContext('block'))
    return


def _define_var(traverser, node):
    'Creates a local context variable'

    traverser._debug('VARIABLE_DECLARATION')
    traverser.debug_level += 1

    declarations = (node['declarations'] if 'declarations' in node
                    else node['head'])

    kind = node.get('kind', 'let')
    for declaration in declarations:

        # It could be deconstruction of variables :(
        if declaration['id']['type'] == 'ArrayPattern':

            vars = []
            for element in declaration['id']['elements']:
                # NOTE : Multi-level array destructuring sucks. Maybe implement
                # it someday if you're bored, but it's so rarely used and it's
                # so utterly complex, there's probably no need to ever code it
                # up.
                if element is None or element['type'] != 'Identifier':
                    vars.append(None)
                    continue
                vars.append(element['name'])

            # The variables are not initialized
            if declaration['init'] is None:
                # Simple instantiation; no initialization
                for var in vars:
                    if not var:
                        continue
                    traverser._declare_variable(var, None)

            # The variables are declared inline
            elif declaration['init']['type'] == 'ArrayPattern':
                # TODO : Test to make sure len(values) == len(vars)
                for value in declaration['init']['elements']:
                    if vars[0]:
                        traverser._declare_variable(
                            vars[0], JSWrapper(traverser._traverse_node(value),
                                               traverser=traverser))
                    vars = vars[1:]  # Pop off the first value

            # It's being assigned by a JSArray (presumably)
            elif declaration['init']['type'] == 'ArrayExpression':

                assigner = traverser._traverse_node(declaration['init'])
                for value in assigner.value.elements:
                    if vars[0]:
                        traverser._declare_variable(vars[0], value)
                    vars = vars[1:]

        elif declaration['id']['type'] == 'ObjectPattern':

            init = traverser._traverse_node(declaration['init'])

            def _proc_objpattern(init_obj, properties):
                for prop in properties:
                    # Get the name of the init obj's member
                    if prop['key']['type'] == 'Literal':
                        prop_name = prop['key']['value']
                    elif prop['key']['type'] == 'Identifier':
                        prop_name = prop['key']['name']
                    else:
                        continue

                    if prop['value']['type'] == 'Identifier':
                        traverser._declare_variable(
                            prop['value']['name'],
                            init_obj.get(traverser, prop_name))
                    elif prop['value']['type'] == 'ObjectPattern':
                        _proc_objpattern(init_obj.get(traverser, prop_name),
                                         prop['value']['properties'])

            if init is not None:
                _proc_objpattern(init_obj=init,
                                 properties=declaration['id']['properties'])

        else:
            var_name = declaration['id']['name']
            traverser._debug('NAME>>%s' % var_name)

            var_value = traverser._traverse_node(declaration['init'])
            traverser._debug('VALUE>>%s' % (var_value.output()
                                            if var_value is not None
                                            else 'None'))

            if not isinstance(var_value, JSWrapper):
                var = JSWrapper(value=var_value,
                                const=kind == 'const',
                                traverser=traverser)
            else:
                var = var_value
                var.const = kind == 'const'

            traverser._declare_variable(var_name, var, type_=kind)

    if 'body' in node:
        traverser._traverse_node(node['body'])

    traverser.debug_level -= 1

    # The "Declarations" branch contains custom elements.
    return True


def _define_obj(traverser, node):
    'Creates a local context object'

    var = JSObject()
    for prop in node['properties']:
        if prop['type'] == 'PrototypeMutation':
            var_name = 'prototype'
        else:
            key = prop['key']
            if key['type'] == 'Literal':
                var_name = key['value']
            elif isinstance(key['name'], basestring):
                var_name = key['name']
            else:
                if 'property' in key['name']:
                    name = key['name']
                else:
                    name = {'property': key['name']}
                var_name = _get_member_exp_property(traverser, name)

        var_value = traverser._traverse_node(prop['value'])
        var.set(var_name, var_value, traverser)

        # TODO: Observe "kind"

    if not isinstance(var, JSWrapper):
        return JSWrapper(var, lazy=True, traverser=traverser)
    var.lazy = True
    return var


def _define_array(traverser, node):
    """Instantiate an array object from the parse tree."""
    arr = JSArray()
    arr.elements = map(traverser._traverse_node, node['elements'])
    return arr


def _define_template_strings(traverser, node):
    """Instantiate an array of raw and cooked template strings."""
    cooked = JSArray()
    cooked.elements = map(traverser._traverse_node, node['cooked'])
    raw = JSArray()
    raw.elements = map(traverser._traverse_node, node['raw'])

    cooked.set('raw', raw, traverser)
    return cooked


def _define_template(traverser, node):
    """Instantiate a template literal."""
    elements = map(traverser._traverse_node, node['elements'])

    return reduce(partial(_binary_op, '+', traverser=traverser), elements)


def _define_literal(traverser, node):
    """
    Convert a literal node in the parse tree to its corresponding
    interpreted value.
    """
    value = node['value']
    if isinstance(value, dict):
        return JSWrapper(JSObject(), traverser=traverser, dirty=True)

    wrapper = JSWrapper(value if value is not None else JSLiteral(None),
                        traverser=traverser)
    test_literal(traverser, wrapper)
    return wrapper


def test_literal(traverser, wrapper):
    """
    Test the value of a literal, in particular only a string literal at the
    moment, against possibly dangerous patterns.
    """
    value = wrapper.get_literal_value()
    if isinstance(value, basestring):
        # Local import to prevent import loop.
        from validator.testcases.regex import (validate_compat_pref,
                                               validate_string)
        validate_string(value, traverser, wrapper=wrapper)
        validate_compat_pref(value, traverser, wrapper=wrapper)


def _call_expression(traverser, node):
    args = node['arguments']
    for arg in args:
        traverser._traverse_node(arg, source='arguments')

    member = traverser._traverse_node(node['callee'])

    if (traverser.filename.startswith('defaults/preferences/') and
        ('name' not in node['callee'] or
         node['callee']['name'] not in (u'pref', u'user_pref'))):

        traverser.err.warning(
            err_id=('testcases_javascript_actions',
                    '_call_expression',
                    'complex_prefs_defaults_code'),
            warning='Complex code should not appear in preference defaults '
                    'files',
            description="Calls to functions other than 'pref' and 'user_pref' "
                        'should not appear in defaults/preferences/ files.',
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)

    if member.is_global and callable(member.value.get('dangerous', None)):
        result = member.value['dangerous'](a=args, t=traverser._traverse_node,
                                           e=traverser.err)
        name = member.value.get('name', '')

        if result and name:
            kwargs = {
                'err_id': ('testcases_javascript_actions', '_call_expression',
                           'called_dangerous_global'),
                'warning': '`%s` called in potentially dangerous manner' %
                           member.value['name'],
                'description':
                    'The global `%s` function was called using a set '
                    'of dangerous parameters. Calls of this nature '
                    'are deprecated.' % member.value['name']}

            if isinstance(result, DESCRIPTION_TYPES):
                kwargs['description'] = result
            elif isinstance(result, dict):
                kwargs.update(result)

            traverser.warning(**kwargs)

    elif (node['callee']['type'] == 'MemberExpression' and
          node['callee']['property']['type'] == 'Identifier'):

        # If we can identify the function being called on any member of any
        # instance, we can use that to either generate an output value or test
        # for additional conditions.
        identifier_name = node['callee']['property']['name']
        if identifier_name in instanceactions.INSTANCE_DEFINITIONS:
            result = instanceactions.INSTANCE_DEFINITIONS[identifier_name](
                        args, traverser, node, wrapper=member)
            return result

    if member.is_global and 'return' in member.value:
        if 'object' in node['callee']:
            member.parent = trace_member(traverser, node['callee']['object'])

        return member.value['return'](wrapper=member, arguments=args,
                                      traverser=traverser)
    return JSWrapper(JSObject(), dirty=True, traverser=traverser)


def _call_settimeout(a, t, e):
    """
    Handler for setTimeout and setInterval. Should determine whether a[0]
    is a lambda function or a string. Strings are banned, lambda functions are
    ok. Since we can't do reliable type testing on other variables, we flag
    those, too.
    """

    if not a:
        return

    if a[0]['type'] in ('FunctionExpression', 'ArrowFunctionExpression'):
        return

    if t(a[0]).callable:
        return

    return {'err_id': ('javascript', 'dangerous_global', 'eval'),
            'description':
                'In order to prevent vulnerabilities, the `setTimeout` '
                'and `setInterval` functions should be called only with '
                'function expressions as their first argument.',
            'signing_help': (
                'Please do not ever call `setTimeout` or `setInterval` with '
                'string arguments. If you are passing a function which is '
                'not being correctly detected as such, please consider '
                'passing a closure or arrow function, which in turn calls '
                'the original function.'),
            'signing_severity': 'high'}


def _call_require(a, t, e):
    """
    Tests for unsafe uses of `require()` in SDK add-ons.
    """

    args, traverse, err = a, t, e

    if not err.metadata.get('is_jetpack') and len(args):
        return

    module = traverse(args[0]).get_literal_value()
    if not isinstance(module, basestring):
        return

    if module.startswith('sdk/'):
        module = module[len('sdk/'):]

    LOW_LEVEL = {
        # Added from bugs 689340, 731109
        'chrome', 'window-utils', 'observer-service',
        # Added from bug 845492
        'window/utils', 'sdk/window/utils', 'sdk/deprecated/window-utils',
        'tab/utils', 'sdk/tab/utils',
        'system/events', 'sdk/system/events',
    }

    if module in LOW_LEVEL:
        err.metadata['requires_chrome'] = True
        return {'warning': 'Usage of low-level or non-SDK interface',
                'description': 'Your add-on uses an interface which bypasses '
                               'the high-level protections of the add-on SDK. '
                               'This interface should be avoided, and its use '
                               'may significantly complicate your review '
                               'process.'}

    if module == 'widget':
        return {'warning': 'Use of deprecated SDK module',
                'description':
                    "The 'widget' module has been deprecated due to a number "
                    'of performance and usability issues, and has been '
                    'removed from the SDK as of Firefox 40. Please use the '
                    "'sdk/ui/button/action' or 'sdk/ui/button/toggle' module "
                    'instead. See '
                    'https://developer.mozilla.org/Add-ons/SDK/High-Level_APIs'
                    '/ui for more information.'}


def _call_create_pref(a, t, e):
    """
    Handler for pref() and user_pref() calls in defaults/preferences/*.js files
    to ensure that they don't touch preferences outside of the "extensions."
    branch.
    """

    # We really need to clean up the arguments passed to these functions.
    traverser = t.im_self

    if not traverser.filename.startswith('defaults/preferences/') or not a:
        return

    instanceactions.set_preference(JSWrapper(JSLiteral(None),
                                             traverser=traverser),
                                   a, traverser)

    value = _get_as_str(t(a[0]))
    return test_preference(value)


def test_preference(value):
    for branch in 'extensions.', 'services.sync.prefs.sync.extensions.':
        if value.startswith(branch) and value.rindex('.') > len(branch):
            return

    return ('Extensions should not alter preferences outside of the '
            "'extensions.' preference branch. Please make sure that "
            "all of your extension's preferences are prefixed with "
            "'extensions.add-on-name.', where 'add-on-name' is a "
            'distinct string unique to and indicative of your add-on.')


def _readonly_top(traverser, right, node_right):
    """Handle the readonly callback for window.top."""
    traverser.notice(
        err_id=('testcases_javascript_actions',
                '_readonly_top'),
        notice='window.top is a reserved variable',
        description='The `top` global variable is reserved and cannot be '
                    'assigned any values starting with Gecko 6. Review your '
                    'code for any uses of the `top` global, and refer to '
                    '%s for more information.' % BUGZILLA_BUG % 654137,
        for_appversions={FIREFOX_GUID: version_range('firefox',
                                                     '6.0a1', '7.0a1'),
                         FENNEC_GUID: version_range('fennec',
                                                    '6.0a1', '7.0a1')},
        compatibility_type='warning',
        tier=5)


def _expression(traverser, node):
    """
    This is a helper method that allows node definitions to point at
    `_traverse_node` without needing a reference to a traverser.
    """
    return traverser._traverse_node(node['expression'])


def _get_this(traverser, node):
    'Returns the `this` object'
    if not traverser.this_stack:
        from predefinedentities import GLOBAL_ENTITIES
        return traverser._build_global('window', GLOBAL_ENTITIES[u'window'])
    return traverser.this_stack[-1]


def _new(traverser, node):
    'Returns a new copy of a node.'

    # We don't actually process the arguments as part of the flow because of
    # the Angry T-Rex effect. For now, we just traverse them to ensure they
    # don't contain anything dangerous.
    args = node['arguments']
    if isinstance(args, list):
        for arg in args:
            traverser._traverse_node(arg, source='arguments')
    else:
        traverser._traverse_node(args)

    elem = traverser._traverse_node(node['callee'])
    if not isinstance(elem, JSWrapper):
        elem = JSWrapper(elem, traverser=traverser)
    if elem.is_global:
        traverser._debug('Making overwritable')
        elem.value = deepcopy(elem.value)
        elem.value['overwritable'] = True
    return elem


def _ident(traverser, node):
    'Initiates an object lookup on the traverser based on an identifier token'

    name = node['name']

    # Ban bits like "newThread"
    test_identifier(traverser, name)

    if traverser._is_defined(name):
        return traverser._seek_variable(name)

    return JSWrapper(JSObject(), traverser=traverser, dirty=True)


def _expr_assignment(traverser, node):
    """Evaluate an AssignmentExpression node."""

    traverser._debug('ASSIGNMENT_EXPRESSION')
    traverser.debug_level += 1

    traverser._debug('ASSIGNMENT>>PARSING RIGHT')
    right = traverser._traverse_node(node['right'])
    right = JSWrapper(right, traverser=traverser)

    # Treat direct assignment different than augmented assignment.
    if node['operator'] == '=':
        from predefinedentities import GLOBAL_ENTITIES, is_shared_scope

        global_overwrite = False
        readonly_value = is_shared_scope(traverser)

        node_left = node['left']
        traverser._debug('ASSIGNMENT:DIRECT(%s)' % node_left['type'])

        if node_left['type'] == 'Identifier':
            # Identifiers just need the ID name and a value to push.
            # Raise a global overwrite issue if the identifier is global.
            global_overwrite = traverser._is_global(node_left['name'])

            # Get the readonly attribute and store its value if is_global
            if global_overwrite:
                global_dict = GLOBAL_ENTITIES[node_left['name']]
                if 'readonly' in global_dict:
                    readonly_value = global_dict['readonly']

            traverser._declare_variable(node_left['name'], right, type_='glob')
        elif node_left['type'] == 'MemberExpression':
            member_object = trace_member(traverser, node_left['object'],
                                         instantiate=True)
            global_overwrite = (member_object.is_global and
                                not ('overwritable' in member_object.value and
                                     member_object.value['overwritable']))
            member_property = _get_member_exp_property(traverser, node_left)
            traverser._debug('ASSIGNMENT:MEMBER_PROPERTY(%s)'
                             % member_property)
            traverser._debug('ASSIGNMENT:GLOB_OV::%s' % global_overwrite)

            # Don't do the assignment if we're facing a global.
            if not member_object.is_global:
                if member_object.value is None:
                    member_object.value = JSObject()

                if not member_object.is_global:
                    member_object.value.set(member_property, right, traverser)
                else:
                    # It's probably better to do nothing.
                    pass

            elif 'value' in member_object.value:
                member_object_value = _expand_globals(traverser,
                                                      member_object).value
                if member_property in member_object_value['value']:

                    # If it's a global and the actual member exists, test
                    # whether it can be safely overwritten.
                    member = member_object_value['value'][member_property]
                    if 'readonly' in member:
                        global_overwrite = True
                        readonly_value = member['readonly']

        traverser._debug('ASSIGNMENT:DIRECT:GLOB_OVERWRITE %s' %
                         global_overwrite)
        traverser._debug('ASSIGNMENT:DIRECT:READONLY %r' %
                         readonly_value)

        if callable(readonly_value):
            readonly_value = readonly_value(traverser, right, node['right'])

        if readonly_value and global_overwrite:

            kwargs = dict(
                err_id=('testcases_javascript_actions',
                        '_expr_assignment',
                        'global_overwrite'),
                warning='Global variable overwrite',
                description='An attempt was made to overwrite a global '
                            'variable in some JavaScript code.')

            if isinstance(readonly_value, DESCRIPTION_TYPES):
                kwargs['description'] = readonly_value
            elif isinstance(readonly_value, dict):
                kwargs.update(readonly_value)

            traverser.warning(**kwargs)

        return right

    lit_right = right.get_literal_value()

    traverser._debug('ASSIGNMENT>>PARSING LEFT')
    left = traverser._traverse_node(node['left'])
    traverser._debug('ASSIGNMENT>>DONE PARSING LEFT')
    traverser.debug_level -= 1

    if isinstance(left, JSWrapper):
        if left.dirty:
            return left

        lit_left = left.get_literal_value()
        token = node['operator']

        # Don't perform an operation on None. Python freaks out
        if lit_left is None:
            lit_left = 0
        if lit_right is None:
            lit_right = 0

        # Give them default values so we have them in scope.
        gleft, gright = 0, 0

        # All of the assignment operators
        operators = {'=': lambda: right,
                     '+=': lambda: lit_left + lit_right,
                     '-=': lambda: gleft - gright,
                     '*=': lambda: gleft * gright,
                     '/=': lambda: 0 if gright == 0 else (gleft / gright),
                     '%=': lambda: 0 if gright == 0 else (gleft % gright),
                     '<<=': lambda: int(gleft) << int(gright),
                     '>>=': lambda: int(gleft) >> int(gright),
                     '>>>=': lambda: float(abs(int(gleft)) >> gright),
                     '|=': lambda: int(gleft) | int(gright),
                     '^=': lambda: int(gleft) ^ int(gright),
                     '&=': lambda: int(gleft) & int(gright)}

        # If we're modifying a non-numeric type with a numeric operator, return
        # NaN.
        if (not isinstance(lit_left, NUMERIC_TYPES) and
                token in NUMERIC_OPERATORS):
            left.set_value(get_NaN(traverser), traverser=traverser)
            return left

        # If either side of the assignment operator is a string, both sides
        # need to be casted to strings first.
        if (isinstance(lit_left, types.StringTypes) or
                isinstance(lit_right, types.StringTypes)):
            lit_left = _get_as_str(lit_left)
            lit_right = _get_as_str(lit_right)

        gleft, gright = _get_as_num(left), _get_as_num(right)

        traverser._debug('ASSIGNMENT>>OPERATION:%s' % token)
        if token not in operators:
            # We don't support that operator. (yet?)
            traverser._debug('ASSIGNMENT>>OPERATOR NOT FOUND', 1)
            return left
        elif token in ('<<=', '>>=', '>>>=') and gright < 0:
            # The user is doing weird bitshifting that will return 0 in JS but
            # not in Python.
            left.set_value(0, traverser=traverser)
            return left
        elif (token in ('<<=', '>>=', '>>>=', '|=', '^=', '&=') and
              (abs(gleft) == float('inf') or abs(gright) == float('inf'))):
            # Don't bother handling infinity for integer-converted operations.
            left.set_value(get_NaN(traverser), traverser=traverser)
            return left

        traverser._debug('ASSIGNMENT::L-value global? (%s)' %
                         ('Y' if left.is_global else 'N'), 1)
        try:
            new_value = operators[token]()
        except Exception:
            traverser.system_error(exc_info=sys.exc_info())
            new_value = None

        # Cap the length of analyzed strings.
        if (isinstance(new_value, types.StringTypes) and
                len(new_value) > MAX_STR_SIZE):
            new_value = new_value[:MAX_STR_SIZE]

        traverser._debug('ASSIGNMENT::New value >> %s' % new_value, 1)
        left.set_value(new_value, traverser=traverser)
        return left

    # Though it would otherwise be a syntax error, we say that 4=5 should
    # evaluate out to 5.
    return right


def _expr_binary(traverser, node):
    'Evaluates a BinaryExpression node.'

    traverser.debug_level += 1

    # Select the proper operator.
    operator = node['operator']
    traverser._debug('BIN_OPERATOR>>%s' % operator)

    # Traverse the left half of the binary expression.
    with traverser._debug('BIN_EXP>>l-value'):
        if (node['left']['type'] == 'BinaryExpression' and
                '__traversal' not in node['left']):
            # Process the left branch of the binary expression directly. This
            # keeps the recursion cap in line and speeds up processing of
            # large chains of binary expressions.
            left = _expr_binary(traverser, node['left'])
            node['left']['__traversal'] = left
        else:
            left = traverser._traverse_node(node['left'])

    # Traverse the right half of the binary expression.
    with traverser._debug('BIN_EXP>>r-value'):
        if (operator == 'instanceof' and
                node['right']['type'] == 'Identifier' and
                node['right']['name'] == 'Function'):
            # We make an exception for instanceof's r-value if it's a
            # dangerous global, specifically Function.
            return JSWrapper(True, traverser=traverser)
        else:
            right = traverser._traverse_node(node['right'])
            traverser._debug('Is dirty? %r' % right.dirty, 1)

    return _binary_op(operator, left, right, traverser)


def _binary_op(operator, left, right, traverser):
    """Perform a binary operation on two pre-traversed nodes."""

    # Dirty l or r values mean we can skip the expression. A dirty value
    # indicates that a lazy operation took place that introduced some
    # nondeterminacy.
    # FIXME(Kris): We should process these as if they're strings anyway.
    if left.dirty:
        return left
    elif right.dirty:
        return right

    # Binary expressions are only executed on literals.
    left = left.get_literal_value()
    right_wrap = right
    right = right.get_literal_value()

    # Coerce the literals to numbers for numeric operations.
    gleft = _get_as_num(left)
    gright = _get_as_num(right)

    operators = {
        '==': lambda: left == right or gleft == gright,
        '!=': lambda: left != right,
        '===': lambda: left == right,  # Be flexible.
        '!==': lambda: type(left) != type(right) or left != right,
        '>': lambda: left > right,
        '<': lambda: left < right,
        '<=': lambda: left <= right,
        '>=': lambda: left >= right,
        '<<': lambda: int(gleft) << int(gright),
        '>>': lambda: int(gleft) >> int(gright),
        '>>>': lambda: float(abs(int(gleft)) >> int(gright)),
        '+': lambda: left + right,
        '-': lambda: gleft - gright,
        '*': lambda: gleft * gright,
        '/': lambda: 0 if gright == 0 else (gleft / gright),
        '%': lambda: 0 if gright == 0 else (gleft % gright),
        'in': lambda: right_wrap.contains(left),
        # TODO : implement instanceof
        # FIXME(Kris): Treat instanceof the same as `QueryInterface`
    }

    output = None
    if (operator in ('>>', '<<', '>>>') and
            (left is None or right is None or gright < 0)):
        output = False
    elif operator in operators:
        # Concatenation can be silly, so always turn undefineds into empty
        # strings and if there are strings, make everything strings.
        if operator == '+':
            if left is None:
                left = ''
            if right is None:
                right = ''
            if isinstance(left, basestring) or isinstance(right, basestring):
                left = _get_as_str(left)
                right = _get_as_str(right)

        # Don't even bother handling infinity if it's a numeric computation.
        if (operator in ('<<', '>>', '>>>') and
                (abs(gleft) == float('inf') or abs(gright) == float('inf'))):
            return get_NaN(traverser)

        try:
            output = operators[operator]()
        except Exception:
            traverser.system_error(exc_info=sys.exc_info())
            output = None

        # Cap the length of analyzed strings.
        if (isinstance(output, types.StringTypes) and
                len(output) > MAX_STR_SIZE):
            output = output[:MAX_STR_SIZE]

        wrapper = JSWrapper(output, traverser=traverser)

        # Test the newly-created literal for dangerous values.
        # This may cause duplicate warnings for strings which
        # already match a dangerous value prior to concatenation.
        test_literal(traverser, wrapper)

        return wrapper

    return JSWrapper(output, traverser=traverser)


def _expr_unary(traverser, node):
    """Evaluate a UnaryExpression node."""

    expr = traverser._traverse_node(node['argument'])
    expr_lit = expr.get_literal_value()
    expr_num = _get_as_num(expr_lit)

    operators = {'-': lambda: -1 * expr_num,
                 '+': lambda: expr_num,
                 '!': lambda: not expr_lit,
                 '~': lambda: -1 * (expr_num + 1),
                 'void': lambda: None,
                 'typeof': lambda: _expr_unary_typeof(expr),
                 'delete': lambda: None}  # We never want to empty the context
    if node['operator'] in operators:
        output = operators[node['operator']]()
    else:
        output = None

    if not isinstance(output, JSWrapper):
        output = JSWrapper(output, traverser=traverser)
    return output


def _expr_unary_typeof(wrapper):
    """Evaluate the "typeof" value for a JSWrapper object."""
    if (wrapper.callable or
        (wrapper.is_global and 'return' in wrapper.value and
         'value' not in wrapper.value)):
        return 'function'

    value = wrapper.value
    if value is None:
        return 'undefined'
    elif isinstance(value, JSLiteral):
        value = value.value
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, long, float)):
            return 'number'
        elif isinstance(value, types.StringTypes):
            return 'string'
    return 'object'


def _get_as_num(value):
    """Return the JS numeric equivalent for a value."""

    if isinstance(value, JSWrapper):
        value = value.get_literal_value()
    if value is None:
        return 0

    try:
        if isinstance(value, types.StringTypes):
            if value.startswith('0x'):
                return int(value, 16)
            else:
                return float(value)
        elif isinstance(value, (int, float, long)):
            return value
        else:
            return int(value)
    except (ValueError, TypeError):
        return 0


def _get_as_str(value):
    """Return the JS string equivalent for a literal value."""

    if isinstance(value, JSWrapper):
        value = value.get_literal_value()
    if value is None:
        return ''

    if isinstance(value, bool):
        return u'true' if value else u'false'
    elif isinstance(value, (int, float, long)):
        if value == float('inf'):
            return u'Infinity'
        elif value == float('-inf'):
            return u'-Infinity'

        # Try to see if we can shave off some trailing significant figures.
        try:
            if int(value) == value:
                return unicode(int(value))
        except ValueError:
            pass
    return unicode(value)
