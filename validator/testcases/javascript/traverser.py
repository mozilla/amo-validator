from collections import defaultdict
import itertools
import re
import sys
import types

from validator.constants import DESCRIPTION_TYPES

from . import actions
from .jstypes import JSContext, JSLiteral, JSObject, JSWrapper
from .nodedefinitions import DEFINITIONS
from .predefinedentities import GLOBAL_ENTITIES


DEBUG = False
IGNORE_POLLUTION = False
POLLUTION_COMPONENTS_PATH = re.compile(r'/?components/.*\.jsm?')
POLLUTION_EXCEPTIONS = set(['Cc', 'Ci', 'Cu', ])


class Traverser(object):
    """Traverses the AST Tree and determines problems with a chunk of JS."""

    def __init__(self, err, filename, start_line=0, context=None,
                 is_jsm=False):
        self.err = err
        self.is_jsm = is_jsm

        self.contexts = []
        self.block_contexts = []
        self.filename = filename
        self.start_line = start_line
        self.polluted = False
        self.line = 1  # Line number
        self.position = 0  # Column number
        self.context = context

        # Can use the `this` object
        self.can_use_this = False
        self.this_stack = []

        # For ordering of function traversal.
        self.function_collection = []

        # For debugging
        self.debug_level = 0

        class DebugLevel(object):
            def __enter__(self_):
                self.debug_level += 1

            def __exit__(self_, type, value, traceback):
                self.debug_level -= 1
        self._debug_level = DebugLevel()

    def _debug(self, data, indent=0):
        """Write a message to the console if debugging is enabled."""
        if DEBUG:
            output = data
            if isinstance(data, JSObject) or isinstance(data, JSContext):
                output = data.output()

            output = unicode(output)
            print ('. ' * (self.debug_level + indent) +
                   output.encode('ascii', 'replace'))

        return self._debug_level

    def run(self, data):
        if DEBUG:
            x = open('/tmp/output.js', 'w')
            x.write(unicode(data))
            x.close()

        self._debug('START>>')
        try:
            self.function_collection.append([])
            self._traverse_node(data)

            func_coll = self.function_collection.pop()
            for func in func_coll:
                func()
        except Exception:
            self.system_error(exc_info=sys.exc_info())
            return

        self._debug('END>>')

        if self.contexts:
            # If we're in debug mode, save a copy of the global context for
            # analysis during unit tests.
            if DEBUG:
                self.err.final_context = self.contexts[0]

            if self.pollutable:
                # Ignore anything in the components/ directory
                if POLLUTION_COMPONENTS_PATH.match(self.filename):
                    return

                # This performs the namespace pollution test.
                global_context_size = sum(
                    1 for name in self.contexts[0].data if
                    name not in POLLUTION_EXCEPTIONS)
                self._debug('Final context size: %d' % global_context_size)

                if (global_context_size > 3 and not self.is_jsm and
                        'is_jetpack' not in self.err.metadata and
                        self.err.get_resource('em:bootstrap') != 'true'):
                    self.err.warning(
                        err_id=('testcases_javascript_traverser', 'run',
                                'namespace_pollution'),
                        warning='JavaScript namespace pollution',
                        description=(
                            'Your add-on contains a large number of global '
                            'variables, which may conflict with other '
                            'add-ons. For more information, see '
                            'http://blog.mozilla.com/addons/2009/01/16/'
                            'firefox-extensions-global-namespace-pollution/'
                            ', or use JavaScript modules.',
                            'List of entities: %s'
                            % ', '.join(self.contexts[0].data.keys())),
                        filename=self.filename)

    def _traverse_node(self, node, source=None):
        if node is None:
            return JSWrapper(JSObject(), traverser=self, dirty=True)

        # Simple caching to prevent retraversal
        if '__traversal' in node and node['__traversal'] is not None:
            return node['__traversal']

        if isinstance(node, types.StringTypes):
            return JSWrapper(JSLiteral(node), traverser=self)

        # Extract location information if it's available
        if 'loc' in node and node['loc'] is not None:
            self.line = self.start_line + int(node['loc']['start']['line'])
            self.position = int(node['loc']['start']['column'])

        if node.get('type') not in DEFINITIONS:
            if node.get('type'):
                key = 'unknown_node_types'
                if key not in self.err.metadata:
                    self.err.metadata[key] = defaultdict(int)

                self.err.metadata[key][node['type']] += 1

            return JSWrapper(JSObject(), traverser=self, dirty=True)

        self._debug('TRAVERSE>>%s' % node['type'])
        self.debug_level += 1

        # Extract properties about the node that we're traversing
        (branches, establish_context, action, returns,
         block_level) = DEFINITIONS[node['type']]

        # If we're supposed to establish a context, do it now
        if establish_context:
            self._push_context()
        elif block_level:
            self._push_block_context()

        # An action allows the traverser to make intelligent decisions based
        # on the function of the code, rather than just the content. If an
        # action is availble, run it and store the output.
        action_result = None
        if action is not None:
            action_result = action(self, node)
            # Special case, for immediate literals, define a source property.
            # Used for determining when literals are passed directly
            # as arguments.
            if node['type'] == 'Literal':
                action_result.value.source = source

            if DEBUG:
                action_debug = 'continue'
                if action_result is not None:
                    action_debug = (action_result.output() if
                                    isinstance(action_result, JSWrapper) else
                                    action_result)
                self._debug('ACTION>>%s (%s)' % (action_debug, node['type']))

        if action_result is None:
            self.debug_level += 1
            # Use the node definition to determine and subsequently traverse
            # each of the branches.
            for branch in branches:
                if branch in node:
                    self._debug('BRANCH>>%s' % branch)
                    b = node[branch]
                    if isinstance(b, list):
                        map(self._traverse_node, b)
                    else:
                        self._traverse_node(b)
            self.debug_level -= 1

        # If we defined a context, pop it.
        if establish_context or block_level:
            self._pop_context()
            # WithStatements declare two blocks: one for the block and one for
            # the object that's being withed. We need both because of `let`s.
            if node['type'] == 'WithStatement':
                self._pop_context()

        self.debug_level -= 1

        # If there is an action and the action returned a value, it should be
        # returned to the node traversal that initiated this node's traversal.
        if returns:
            if not isinstance(action_result, JSWrapper):
                return JSWrapper(action_result, traverser=self)
            node['__traversal'] = action_result
            return action_result

        node['__traversal'] = None
        return JSWrapper(JSObject(), traverser=self, dirty=True)

    def _push_block_context(self):
        'Adds a block context to the current interpretation frame'
        self.contexts.append(JSContext('block'))

    def _push_context(self, default=None):
        'Adds a variable context to the current interpretation frame'

        if default is None:
            default = JSContext('default')
        self.contexts.append(default)

        self.debug_level += 1
        self._debug('CONTEXT>>%d' % len(self.contexts))

    def _pop_context(self):
        'Adds a variable context to the current interpretation frame'

        # Keep the global scope on the stack.
        if len(self.contexts) == 1:
            self._debug('CONTEXT>>ROOT POP ABORTED')
            return
        popped_context = self.contexts.pop()

        self.debug_level -= 1
        self._debug('POP_CONTEXT>>%d' % len(self.contexts))
        self._debug(popped_context)

    def _peek_context(self, depth=1):
        """Returns the most recent context. Note that this should NOT be used
        for variable lookups."""

        return self.contexts[len(self.contexts) - depth]

    def _seek_variable(self, variable):
        'Returns the value of a variable that has been declared in a context'

        self._debug('SEEK>>%s' % variable)

        # Look for the variable in the local contexts first
        local_variable = self._seek_local_variable(variable)
        if local_variable is not None:
            # If this variable is also global maintain the xpcom_wildcard value
            # so that it stays linked to its entities. This handles a bug where
            # something like `var Cc = Components.classes` would cause
            # references to `Cc['@some/class']` to not find the right entity.
            if (variable in GLOBAL_ENTITIES and
                    isinstance(local_variable.value, dict)):
                global_variable = self._build_global(
                    variable, GLOBAL_ENTITIES[variable])
                if 'xpcom_wildcard' in global_variable.value:
                    local_variable.value['xpcom_wildcard'] = (
                        global_variable.value['xpcom_wildcard'])
            return local_variable

        # Seek in globals for the variable instead.
        self._debug('SEEK_GLOBAL>>%s' % variable)
        if self._is_global(variable):
            self._debug('SEEK_GLOBAL>>FOUND>>%s' % variable)
            return self._build_global(variable, GLOBAL_ENTITIES[variable])

        self._debug('SEEK_GLOBAL>>FAILED')
        # If we can't find a variable, we always return a dummy object.
        return JSWrapper(JSObject(), traverser=self)

    def _is_defined(self, variable):
        return variable in GLOBAL_ENTITIES or self._is_local_variable(variable)

    def _is_local_variable(self, variable):
        """Return whether a variable is defined in the current scope."""
        return any(ctx.has_var(variable) for ctx in self.contexts)

    def _seek_local_variable(self, variable):
        # Loop through each context in reverse order looking for the defined
        # variable.
        for context in reversed(self.contexts):
            # If it has the variable, return it.
            if context.has_var(variable):
                self._debug('SEEK>>FOUND')
                return context.get(variable, traverser=self)

    def _is_global(self, name):
        'Returns whether a name is a global entity'
        return not self._is_local_variable(name) and name in GLOBAL_ENTITIES

    def _build_global(self, name, entity):
        'Builds an object based on an entity from the predefined entity list'

        if (not callable(entity.get('dangerous')) or
                'dangerous_on_read' in entity):
            dang = entity.get('dangerous', entity.get('dangerous_on_read'))

            if callable(dang):
                dang = dang(self._traverse_node, self.err)

            if dang:
                kwargs = dict(
                    err_id=('js', 'traverser', 'dangerous_global'),
                    warning='Access to the `%s` global' % name,
                    description='Access to the `%s` property is '
                                'deprecated for security or '
                                'other reasons.' % name)

                if isinstance(dang, DESCRIPTION_TYPES):
                    kwargs['description'] = dang
                elif isinstance(dang, dict):
                    kwargs.update(dang)

                self._debug('DANGEROUS')
                self.warning(**kwargs)

        entity.setdefault('name', name)

        # Build out the wrapper object from the global definition.
        result = JSWrapper(is_global=True, traverser=self, lazy=True)
        result.value = entity.copy()
        result = actions._expand_globals(self, result)

        if 'context' in entity:
            result.context = entity['context']

        self._debug('BUILT_GLOBAL')

        return result

    def _declare_variable(self, name, value, type_='var'):
        context = None
        if type_ in ('var', 'const', ):
            # Same as `reversed(self.contexts[1:])`
            for cont in itertools.islice(reversed(self.contexts), None,
                                         len(self.contexts)):
                if cont.type_ == 'default':
                    context = cont
                    break
            else:
                context = self.contexts[0]
        elif type_ == 'let':
            context = self.contexts[-1]
        elif type_ == 'glob':
            # Look down through the lexical scope. If the variable being
            # assigned is present in one of those objects, use that as the
            # target context.
            for ctx in reversed(self.contexts[1:]):
                if ctx.has_var(name):
                    context = ctx
                    break

        if not context:
            context = self.contexts[0]

        context.set(name, value)
        return value

    def _err_kwargs(self, kwargs):
        err_kwargs = {
            'filename': self.filename,
            'line': self.line,
            'column': self.position,
            'context': self.context,
        }
        err_kwargs.update(kwargs)
        return err_kwargs

    def error(self, **kwargs):
        err_kwargs = self._err_kwargs(kwargs)
        return self.err.error(**err_kwargs)

    def warning(self, **kwargs):
        err_kwargs = self._err_kwargs(kwargs)
        return self.err.warning(**err_kwargs)

    def notice(self, **kwargs):
        err_kwargs = self._err_kwargs(kwargs)
        return self.err.notice(**err_kwargs)

    def system_error(self, **kwargs):
        err_kwargs = self._err_kwargs(kwargs)
        return self.err.system_error(**err_kwargs)
