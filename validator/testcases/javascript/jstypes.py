import types
import instanceproperties

from validator.constants import JETPACK_URI_URL


class JSObject(object):
    """
    Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements.
    """

    def __init__(self, data=None, unwrapped=False):
        self.type_ = 'object'  # For use when an object is pushed as a context.
        self.data = {u'prototype': lambda: JSPrototype()}
        if data:
            self.data.update(data)
        self.messages = []
        self.is_unwrapped = unwrapped

        self.recursing = False

    def get(self, name, instantiate=False, traverser=None):
        'Returns the value associated with a property name'
        name = unicode(name)
        output = None

        if name == 'wrappedJSObject':
            if traverser:
                traverser._debug('Requested unwrapped JS object...')
            clone = JSObject(unwrapped=True)
            clone.data = self.data
            return JSWrapper(clone, traverser=traverser)

        if name in self.data:
            output = self.data[name]
            if callable(output):
                output = output()
        elif instantiate:
            output = JSWrapper(JSObject(), dirty=True, traverser=traverser)
            self.set(name, output, traverser=traverser)

        if traverser:
            modifier = instanceproperties.get_operation('get', name)
            if modifier:
                modifier(traverser)

        if output is None:
            return JSWrapper(JSObject(), dirty=True, traverser=traverser)
        if not isinstance(output, JSWrapper):
            output = JSWrapper(output, traverser=traverser)
        return output

    def get_literal_value(self):
        return u'[object Object]'

    def set(self, name, value, traverser=None):
        if traverser:
            modifier = instanceproperties.get_operation('set', name)
            if modifier:
                modified_value = modifier(value, traverser)
                if modified_value is not None:
                    value = modified_value

            if self.is_unwrapped:
                traverser.warning(
                    err_id=('testcases_javascript_jstypes', 'JSObject_set',
                            'unwrapped_js_object'),
                    warning="Assignment of unwrapped JS Object's properties.",
                    description='Improper use of unwrapped JS objects can '
                                'result in serious security vulnerabilities. '
                                'Please reconsider your use of unwrapped '
                                'JS objects.',
                    signing_help='Please avoid assigning to properties of '
                                 'unwrapped objects from unprivileged scopes, '
                                 'unless you are using an export API '
                                 '(http://mzl.la/1fvvgm9) to expose API '
                                 'functions to content scopes. '
                                 'In this case, however, please note that '
                                 'your add-on will be required to undergo '
                                 'manual code review for at least one '
                                 'submission.',
                    signing_severity='high')

        self.data[name] = value

    def has_var(self, name):
        name = unicode(name)
        return name in self.data

    def output(self):
        if self.recursing:
            return u'(recursion)'

        # Prevent unruly recursion with a recursion buster.
        self.recursing = True

        output_dict = {}
        for key in self.data.keys():
            if callable(self.data[key]):
                continue
            elif (isinstance(self.data[key], JSWrapper) and
                  self.data[key].value == self):
                output_dict[key] = u'(self)'
            elif self.data[key] is None:
                output_dict[key] = u'(None)'
            else:
                output_dict[key] = self.data[key].output()

        # Pop from the recursion buster.
        self.recursing = False

        output = []
        if self.is_unwrapped:
            output.append('<unwrapped>: ')
        output.append(str(output_dict))
        return ''.join(output)


class JSContext(JSObject):
    """A variable context"""

    def __init__(self, context_type, unwrapped=False):
        super(JSContext, self).__init__(unwrapped=unwrapped)
        self.type_ = context_type
        self.data = {}


class JSWrapper(object):
    """Wraps a JS value and handles contextual functions for it."""

    def __init__(self, value=None, const=False, dirty=False, lazy=False,
                 is_global=False, traverser=None, callable=False,
                 setter=None, context='chrome'):

        if is_global:
            assert not value

        if traverser is not None:
            traverser.debug_level += 1
            traverser._debug('-----New JSWrapper-----')
            if isinstance(value, JSWrapper):
                traverser._debug('>>> Rewrap <<<')
            traverser.debug_level -= 1

        self.const = const
        self.traverser = traverser
        self.value = None  # Instantiate the placeholder value
        self.is_global = False  # Not yet...
        self.dirty = False  # Also not yet...
        self.context = context

        # Used for predetermining set operations
        self.setter = setter

        if value is not None:
            self.set_value(value, overwrite_const=True)

        if not self.is_global:
            self.is_global = is_global  # Globals are built seperately

        self.dirty = dirty or self.dirty
        self.lazy = lazy
        self.callable = callable

        # This will be set in actions.py if needed.
        self.global_parent = False

    def set_value(self, value, traverser=None, overwrite_const=False):
        """Assigns a value to the wrapper"""

        # Use a global traverser if it's present.
        if traverser is None:
            traverser = self.traverser

        if self.const and not overwrite_const:
            traverser.err.warning(
                err_id=('testcases_javascript_traverser',
                        'JSWrapper_set_value', 'const_overwrite'),
                warning='Overwritten constant value',
                description='A variable declared as constant has been '
                            'overwritten in some JS code.',
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)

        # Process any setter/modifier
        if self.setter:
            traverser._debug('Running setter on JSWrapper...')
            value = self.setter(value, traverser) or value or None

        if value == self.value:
            return self

        # We want to obey the permissions of global objects
        if (self.is_global and
            (not traverser or
             not (traverser.is_jsm or
                  traverser.err.get_resource('em:bootstrap') == 'true')) and
            (isinstance(self.value, dict) and
             not self.value.get('overwriteable', True))):
            traverser.err.warning(
                err_id=('testcases_javascript_jstypes', 'JSWrapper_set_value',
                        'global_overwrite'),
                warning='Global overwrite',
                description='An attempt to overwrite a global variable was '
                            'made in some JS code.',
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)
            return self

        if isinstance(value, (bool, str, int, float, long, unicode)):
            self.inspect_literal(value)
            value = JSLiteral(value)
        # If the value being assigned is a wrapper as well, copy it in
        elif isinstance(value, JSWrapper):
            self.value = value.value
            self.lazy = value.lazy
            self.dirty = value.dirty
            self.is_global = value.is_global
            self.context = value.context
            # const does not carry over on reassignment
            return self
        elif callable(value):
            value = value(t=traverser)

        if not isinstance(value, dict):
            self.is_global = False
        elif 'context' in value:
            self.context = value['context']

        self.value = value
        return self

    def has_property(self, property):
        """Returns a boolean value representing the presence of a property"""
        if isinstance(self.value, JSLiteral):
            return False
        return isinstance(self.value, JSObject)

    def get(self, traverser, name, instantiate=False):
        """Retrieve a property from the variable."""

        value = self.value
        dirty = value is None
        context = self.context
        if self.is_global:
            if 'value' not in value:
                output = JSWrapper(JSObject(), traverser=traverser)
                output.value = {}

                def apply_value(name):
                    if name in self.value:
                        output.value[name] = self.value[name]

                map(apply_value, ('dangerous', 'readonly', 'context', 'name'))
                output.is_global = True
                output.context = self.context
                return output

            def _evaluate_lambdas(node):
                if callable(node):
                    return _evaluate_lambdas(node(t=traverser))
                else:
                    return node

            value_val = value['value']
            value_val = _evaluate_lambdas(value_val)

            if isinstance(value_val, dict):
                if name in value_val:
                    value_val = _evaluate_lambdas(value_val[name])
                    output = traverser._build_global(name=name,
                                                     entity=value_val)
                    if 'context' not in value_val:
                        output.context = self.context
                    return output
            else:
                value = value_val

        # Process any getters that are present for the current property.
        modifier = instanceproperties.get_operation('get', name)
        if modifier:
            modifier(traverser)

        if value is not None and issubclass(type(value), JSObject):
            output = value.get(name, instantiate=instantiate,
                               traverser=traverser)
        else:
            output = None

        if not isinstance(output, JSWrapper):
            output = JSWrapper(
                output, traverser=traverser, dirty=output is None or dirty)

        output.context = context

        # If we can predetermine the setter for the wrapper, we can save a ton
        # of lookbehinds in the future. This greatly simplifies the
        # MemberExpression support.
        setter = instanceproperties.get_operation('set', name)
        if setter:
            output.setter = setter
        return output

    def del_value(self, member):
        """The member `member` will be deleted from the value of the wrapper"""
        if self.is_global:
            self.traverser.err.warning(
                err_id=('testcases_js_jstypes', 'del_value',
                        'global_member_deletion'),
                warning='Global member deletion',
                description='Members of global object may not be deleted.',
                filename=self.traverser.filename,
                line=self.traverser.line,
                column=self.traverser.position,
                context=self.traverser.context)
            return
        elif isinstance(self.value, (JSObject, JSPrototype)):
            if member not in self.value.data:
                return
            del self.value.data[member]

    def contains(self, value):
        """Serves 'in' for BinaryOperators for lists and dictionaries"""

        # Unwrap the rvalue.
        if isinstance(value, JSWrapper):
            value = value.get_literal_value()

        if isinstance(self.value, JSArray):
            from actions import _get_as_num
            index = int(_get_as_num(value))
            if len(self.value.elements) > index >= 0:
                return True

        if isinstance(self.value, (JSArray, JSObject, JSPrototype)):
            return self.value.has_var(value)

        # Nothing else supports "in"
        return False

    def is_literal(self):
        """Returns whether the content is a literal"""
        return isinstance(self.value, JSLiteral)

    def get_literal_value(self):
        """Returns the literal value of the wrapper"""

        if self.is_global:
            if 'literal' in self.value:
                return self.value['literal'](self.traverser)
            else:
                return '[object Object]'
        if self.value is None:
            return None

        output = self.value.get_literal_value()
        return output

    def output(self):
        """Returns a readable version of the object"""
        if self.value is None:
            return '(None)'
        elif self.is_global:
            return '(Global)'

        return self.value.output()

    def inspect_literal(self, value):
        """
        Inspect the value of a literal to see whether it contains a flagged
        value.
        """

        # Don't do any processing if we can't return an error.
        if not self.traverser:
            return

        self.traverser._debug('INSPECTING: %s' % value)

        if isinstance(value, types.StringTypes):
            if ('is_jetpack' in self.traverser.err.metadata and
                    value.startswith('resource://') and
                    '-data/' in value):
                # Since Jetpack files are ignored, this should not be scanning
                # anything inside the jetpack directories.
                self.traverser.warning(
                    err_id=('javascript_js_jstypes', 'jswrapper',
                            'jetpack_abs_uri'),
                    warning='Absolute URIs in Jetpack 1.4 are disallowed',
                    description=('As of Jetpack 1.4, absolute URIs are no '
                                 'longer allowed within add-ons.',
                                 'See %s for more information.'
                                 % JETPACK_URI_URL),
                    compatibility_type='error')

    def __unicode__(self):
        """Returns a textual version of the object."""
        return unicode(self.get_literal_value())


class JSLiteral(JSObject):
    """Represents a literal JavaScript value."""

    def __init__(self, value=None, unwrapped=False):
        super(JSLiteral, self).__init__(unwrapped=unwrapped)
        self.value = value
        self.source = None

    def set_value(self, value):
        self.value = value

    def __str__(self):
        if isinstance(self.value, bool):
            return str(self.output()).lower()
        return str(self.output())

    def output(self):
        return self.value

    def get_literal_value(self):
        'Returns the literal value of a this literal. Heh.'
        return self.value


class JSPrototype(JSObject):
    """
    A lazy JavaScript object that is assumed not to contain any default
    methods.
    """

    def __init__(self, unwrapped=False):
        super(JSPrototype, self).__init__(unwrapped=unwrapped)
        self.data = {}

    def get(self, name, instantiate=False, traverser=None):
        name = unicode(name)
        output = super(JSPrototype, self).get(name, instantiate, traverser)
        if output is not None:
            return output
        if name == 'prototype':
            prototype = JSWrapper(JSPrototype(), traverser=traverser)
            self.data[name] = prototype

        return output


class JSArray(JSObject):
    """A class that represents both a JS Array and a JS list."""

    def __init__(self, unwrapped=False):
        super(JSArray, self).__init__(unwrapped=unwrapped)
        self.elements = []

    def get(self, index, instantiate=False, traverser=None):
        if index == 'length':
            return len(self.elements)

        # Courtesy of Ian Bicking: http://bit.ly/hxv6qt
        try:
            output = self.elements[int(index.strip().split()[0])]
            if not isinstance(output, JSWrapper):
                output = JSWrapper(output, traverser=traverser)
            return output
        except (ValueError, IndexError, KeyError):
            return super(JSArray, self).get(index, instantiate, traverser)

    def get_literal_value(self):
        """Arrays return a comma-delimited version of themselves."""

        if self.recursing:
            return u'(recursion)'

        self.recursing = True

        # Interestingly enough, this allows for things like:
        # x = [4]
        # y = x * 3 // y = 12 since x equals "4"

        output = u','.join(
            [unicode(w.get_literal_value() if w is not None else u'') for w in
             self.elements if
             not (isinstance(w, JSWrapper) and w.value == self)])

        self.recursing = False
        return output

    def set(self, index, value, traverser=None):
        try:
            index = int(index)
            # Ignore floating point indexes
            if index != float(index) or index < 0:
                return super(JSArray, self).set(value, traverser)
        except ValueError:
            return super(JSArray, self).set(index, value, traverser)

        if len(self.elements) > index:
            self.elements[index] = JSWrapper(value=value, traverser=traverser)
        else:
            # Max out the array size at 100000
            index = min(index, 100000)
            # Assigning to an index higher than the top of the list pads the
            # list with nulls
            while len(self.elements) < index:
                self.elements.append(None)
            self.elements.append(JSWrapper(value=value, traverser=traverser))

    def output(self):
        return u'[%s]' % self.get_literal_value()
