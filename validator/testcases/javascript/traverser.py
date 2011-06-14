import json
import types

from validator.testcases.javascript.jstypes import *
from validator.testcases.javascript.nodedefinitions import DEFINITIONS
from validator.testcases.javascript.predefinedentities import \
               GLOBAL_ENTITIES, BANNED_IDENTIFIERS

DEBUG = False
IGNORE_POLLUTION = False


class MockBundler:
    """A delightful replacement for the ErrorBundler, especially while
    performing non-unit test debugging operations"""

    def __init__(self):
        self.message_count = 0
        self.final_context = None
        self.tier = 4
        self.ids = []
        self.detected_type = 1
        self.resources = {}

    def failed(self):
        "Returns whether messages have been reported"
        return bool(self.message_count)

    def set_tier(self, tier):
        "Sets the tier; compatibility with ErrorBundle"
        self.tier = tier

    def save_resource(self, name, data):
        """Saves a blob of data to be accessed later."""
        self.resources[name] = data

    def get_resource(self, name):
        """Retrieves a saved blob of data."""
        return self.resources[name] if name in self.resources else False

    def error(self, err_id, error, description, filename="",
              line=1, column=0, context=None):
        "Represents a mock error"

        # Increment the message counter
        self.message_count += 1

        self.ids.append(err_id)

        error = unicode(error)

        print "-" * 30
        print error.encode("ascii", "replace")
        print "~" * len(error)
        if isinstance(description, types.StringTypes):
            print description
        else:
            # Errors can have multiple lines
            for dline in description:
                # Each line can have multiple lines :(
                dline = dline.replace("\n", " ")
                while dline.count("  "):
                    # Strip out extraneous whitespace!
                    dline = dline.replace("  ", " ")

                print dline
        print "in %s:line %d (%d)" % (file, line, column)

    def warning(self, err_id, warning, description, filename="",
                line=1, column=0, context=None):
        self.error(err_id, warning, description, file, line, column, context)

    def notice(self, err_id, notice, description, filename="",
               line=1, column=0, context=None):
        self.error(err_id, notice, description, file, line, column, context)

    def info(self, id, title, description, filename="",
             line=1, column=0, context=None):
        print "Obsolete use of 'info'"
        assert None
        self.error(id, title, description, file, line, column, context)


class Traverser:
    "Traverses the AST Tree and determines problems with a chunk of JS."

    def __init__(self, err, filename, start_line=0, context=None,
                 is_jsm=False):
        if err is not None:
            self.err = err
        else:
            self.err = MockBundler()

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

        # For debugging
        self.debug_level = 0

    def _debug(self, data):
        "Writes a message to the console if debugging is enabled."
        if DEBUG:
            output = data
            if isinstance(data, JSObject) or isinstance(data, JSContext):
                output = data.output()

            output = unicode(output)
            print ". " * self.debug_level + output.encode("ascii", "replace")

    def run(self, data):
        if DEBUG:
            x = open("/tmp/output.js", "w")
            x.write(unicode(data))
            x.close()

        if "type" not in data or not self._can_handle_node(data["type"]):
            self._debug("ERR>>Cannot handle node type %s" %
                            (data["type"] if "type" in data else "<unknown>"))
            return None

        self._debug("START>>")

        self._traverse_node(data)

        self._debug("END>>")

        if self.contexts:
            # If we're in debug mode, save a copy of the global context for
            # analysis during unit tests.
            if DEBUG:
                self.err.final_context = self.contexts[0]

            if not IGNORE_POLLUTION:
                # This performs the namespace pollution test.
                global_context_size = len(self.contexts[0].data)
                self._debug("Final context size: %d" % global_context_size)

                if global_context_size > 3 and not self.is_jsm:
                    self.err.warning(
                        err_id=("testcases_javascript_traverser",
                                "run",
                                "namepsace_pollution"),
                        warning="JavaScript namespace pollution",
                        description=["Your add-on contains a large number of "
                                     "global variables, which can conflict "
                                     "with other add-ons. For more "
                                     "information, see "
                                "http://blog.mozilla.com/addons/2009/01/16/"
                                "firefox-extensions-global-namespace-pollution/"
                                     ", or use JavaScript modules.",
                                     "List of entities: %s" %
                                         ", ".join(self.contexts[0].data.keys())],
                       filename=self.filename)

    def _can_handle_node(self, node_name):
        "Determines whether a node can be handled."
        return node_name in DEFINITIONS

    def _traverse_node(self, node):
        "Finds a node's internal blocks and helps manage state."

        if node is None:
            return None

        # Simple caching to prevent retraversal
        if "__traversal" in node:
            return node["__traversal"]

        # Handles all the E4X stuff and anything that may or may not return
        # a value.
        if "type" not in node or not self._can_handle_node(node["type"]):
            wrapper = JSWrapper(traverser=self)
            wrapper.set_value(JSObject())
            return wrapper

        self._debug("TRAVERSE>>%s" % (node["type"]))
        self.debug_level += 1

        # Extract location information if it's available
        if "loc" in node and node["loc"] is not None:
            self.line = self.start_line + int(node["loc"]["start"]["line"])
            self.position = int(node["loc"]["start"]["column"])

        # Extract properties about the node that we're traversing
        (branches,
         explicitly_dynamic,
         establish_context,
         action,
         returns,
         block_level) = DEFINITIONS[node["type"]]

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

            if DEBUG:
                action_debug = "continue"
                if action_result is not None:
                    action_debug = (action_result.output() if
                                    isinstance(action_result, JSWrapper) else
                                    action_result)
                self._debug("ACTION>>%s (%s)" % (action_debug,
                                                 node["type"]))

        # print node["type"], branches
        if action_result is None:
            self.debug_level += 1
            # Use the node definition to determine and subsequently traverse
            # each of the branches.
            for branch in branches:
                if branch in node:
                    self._debug("BRANCH>>%s" % branch)
                    self.debug_level += 1
                    b = node[branch]
                    if isinstance(b, list):
                        self._interpret_block(b)
                    else:
                        self._traverse_node(b)
                    self.debug_level -= 1
            self.debug_level -= 1

        # If we defined a context, pop it.
        if establish_context or block_level:
            self._pop_context()

        self.debug_level -= 1

        # If there is an action and the action returned a value, it should be
        # returned to the node traversal that initiated this node's traversal.
        if returns:
            if not isinstance(action_result, JSWrapper):
                return JSWrapper(action_result, traverser=self)
            node["__traversal"] = action_result
            return action_result

        node["__traversal"] = None

    def _interpret_block(self, items):
        "Interprets a block of consecutive code"

        for item in items:
            self._traverse_node(item)

        # Iterative code will never return a value.

    def _push_block_context(self):
        "Adds a block context to the current interpretation frame"
        self.contexts.append(JSContext("block"))

    def _push_context(self, default=None):
        "Adds a variable context to the current interpretation frame"

        if default is None:
            default = JSContext("default")
        self.contexts.append(default)

        self.debug_level += 1
        self._debug("CONTEXT>>%d" % len(self.contexts))

    def _pop_context(self):
        "Adds a variable context to the current interpretation frame"

        # Keep the global scope on the stack.
        if len(self.contexts) == 1:
            self._debug("CONTEXT>>ROOT POP ABORTED")
            return
        popped_context = self.contexts.pop()

        self.debug_level -= 1
        self._debug("POP_CONTEXT>>%d" % len(self.contexts))
        self._debug(popped_context)

    def _peek_context(self, depth=1):
        """Returns the most recent context. Note that this should NOT be used
        for variable lookups."""

        return self.contexts[len(self.contexts) - depth]

    def _seek_variable(self, variable, depth=-1):
        "Returns the value of a variable that has been declared in a context"

        self._debug("SEEK>>%s>>%d" % (variable, depth))

        # Look for the variable in the local contexts first
        local_variable = self._seek_local_variable(variable, depth)
        if local_variable is not None:
            if not isinstance(local_variable, JSWrapper):
                return JSWrapper(local_variable, traverser=self)
            return local_variable

        self._debug("SEEK_FAIL>>TRYING GLOBAL")

        # Seek in globals for the variable instead.
        return self._get_global(variable)

    def _is_local_variable(self, variable):
        "Returns whether a variable is defined in the current scope"

        context_count = len(self.contexts)
        for c in range(context_count):
            context = self.contexts[context_count - c - 1]
            if context.has_var(variable):
                return True

        return False

    def _seek_local_variable(self, variable, depth=-1):
        # Loop through each context in reverse order looking for the defined
        # variable.
        context_count = len(self.contexts)
        for c in range(context_count):
            context = self.contexts[context_count - c - 1]

            # If it has the variable, return it
            if context.has_var(variable):
                self._debug("SEEK>>FOUND AT DEPTH %d" % c)
                var = context.get(variable)
                if not isinstance(var, JSWrapper):
                    return JSWrapper(var, traverser=self)
                return var

            # Decrease the level that's being searched through. If we've
            # reached the bottom (relative to where the user defined it to be),
            # end the search.
            depth -= 1
            if depth == -1:
                return JSWrapper(traverser=self)

    def _is_global(self, name, globs=None):
        "Returns whether a name is a global entity"

        if globs is None:
            globs = GLOBAL_ENTITIES

        return name in globs

    def _get_global(self, name, globs=None):
        "Gets a variable from the predefined variable context."

        # Allow overriding of the global entities
        if globs is None:
            globs = GLOBAL_ENTITIES

        self._debug("SEEK_GLOBAL>>%s" % name)
        if not self._is_global(name, globs):
            self._debug("SEEK_GLOBAL>>FAILED")
            return JSWrapper(traverser=self)

        self._debug("SEEK_GLOBAL>>FOUND>>%s" % name)
        return self._build_global(name, globs[name])

    def _build_global(self, name, entity):
        "Builds an object based on an entity from the predefined entity list"

        if "dangerous" in entity:
            dang = entity["dangerous"]
            if dang and not isinstance(dang, types.LambdaType):
                self._debug("DANGEROUS")
                self.err.warning(("testcases_javascript_traverser",
                                  "_build_global",
                                  "dangerous_global"),
                                 "Dangerous Global Object",
                                 [dang if
                                  isinstance(dang, types.StringTypes) else
                                  "A dangerous or banned global object was "
                                  "accessed by some JavaScript code.",
                                  "Accessed object: %s" % name],
                                 self.filename,
                                 line=self.line,
                                 column=self.position,
                                 context=self.context)

        # Build out the wrapper object from the global definition.
        result = JSWrapper(is_global=True, traverser=self, lazy=True)
        result.value = entity

        self._debug("BUILT_GLOBAL")

        return result

    def _set_variable(self, name, value, glob=False):
        "Sets the value of a variable/object in the local or global scope."

        self._debug("SETTING_OBJECT")

        context_count = len(self.contexts)
        for i in range(context_count):
            context = self.contexts[context_count - i - 1]
            if context.has_var(name):
                self._debug("SETTING_OBJECT>>LOCAL>>%d" % i)
                context.set(name, value)
                return value

        self._debug("SETTING_OBJECT>>LOCAL")
        self.contexts[0 if glob else -1].set(name, value)
        return value

