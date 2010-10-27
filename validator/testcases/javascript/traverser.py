import json
import types

from validator.testcases.javascript.nodedefinitions import DEFINITIONS
from validator.testcases.javascript.predefinedentities import GLOBAL_ENTITIES

DEBUG = True

class MockBundler:
    def error(self, id, title, description, file="", line=1):
        "Represents a mock error"
        print "-" * 30
        print title
        print "~" * len(title)
        if isinstance(description, str):
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
        print "in %s:line %d" % (file, line)

    def warning(self, id, title, description, file="", line=1):
        self.error(id, title, description, file, line)

    def info(self, id, title, description, file="", line=1):
        self.error(id, title, description, file, line)


class Traverser:
    "Traverses the AST Tree and determines problems with a chunk of JS."
    
    def __init__(self, err, filename, start_line=0):
        if err is not None:
            self.err = err
        else:
            self.err = MockBundler()
        self.contexts = []
        self.block_contexts = []
        self.filename = filename
        self.start_line = start_line
        self.polluted = False
        self.line = 0
        
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
            print ". " * self.debug_level + output

    def run(self, data):
        if DEBUG:
            x = open("/tmp/output.js", "w")
            x.write(str(data))
            x.close()

        if "type" not in data or not self._can_handle_node(data["type"]):
            self._debug("ERR>>Cannot handle node type %s" % (data["type"] if
                                                             "type" in data
                                                             else "<unknown>"))
            self.err.error(("testcases_javascript_traverser",
                            "run",
                            "cannot_interpret_js"),
                           "Cannot interpret JavaScript",
                           """Some JavaScript code was found, but could not be
                           interpreted.""",
                           self.filename,
                           self.start_line)
            return None
        
        self._debug("START>>")
        
        self._traverse_node(data)
        
        self._debug("END>>")

        if self.contexts:
            # This performs the namespace pollution test.
            # {prefix, count}
            prefixes = []
            global_ns = self.contexts[0]
            for name in global_ns.__dict__.keys():
                pass
    
    def _can_handle_node(self, node_name):
        "Determines whether a node can be handled."
        return node_name in DEFINITIONS
    
    def _traverse_node(self, node):
        "Finds a node's internal blocks and helps manage state."
        
        if node is None:
            return None
        
        # Handles all the E4X stuff and anythign that may or may not return
        # a value.
        if "type" not in node or not self._can_handle_node(node["type"]):
            wrapper = JSWrapper(None)
            wrapper.set_value(JSObject())
            return wrapper
        
        self._debug("TRAVERSE>>%s" % (node["type"]))

        self.line = self.start_line + int(node["loc"]["start"]["line"])
        
        (branches,
         explicitly_dynamic,
         establish_context,
         action,
         returns,
         block_level) = DEFINITIONS[node["type"]]
        
        if establish_context:
            self._push_context()
        elif block_level:
            self._push_block_context()
        
        action_result = None
        if action is not None:
            action_result = action(self, node)
            self._debug("ACTION>>%s" %
                    (str("halt") if action_result else "continue"))
        
        if not action_result:
            self.debug_level += 1
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
        
        if establish_context or block_level:
            self._pop_context()
        
        if returns:
            wrapper = JSWrapper(None)
            wrapper.set_value(self, action_result)
    
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
        
        return self.contexts[:0 - depth]
        
    def _seek_variable(self, variable, depth=-1, args=None):
        "Returns the value of a variable that has been declared in a context"
        
        self._debug("SEEK>>%s>>%d" % (variable, depth))
        
        # Look for the variable in the local contexts first
        local_variable = self._seek_local_variable(variable, depth)
        if local_variable is not None:
            return JSWrapper(local_variable)

        self._debug("SEEK_FAIL>>TRYING GLOBAL")

        # Seek in globals for the variable instead.
        return JSWrapper(self._get_global(variable, args))


    def _seek_local_variable(self, variable, depth=-1):
        
        # Loop through each context in reverse order looking for the defined
        # variable.
        for c in range(0, len(self.contexts) - 1):
            context = self.contexts[len(self.contexts) - 1 - c]

            # If it has the variable, return it
            if context.has_var(variable):
                self._debug("SEEK>>FOUND AT DEPTH %d" % c)
                return context.get(variable)

            # Decrease the level that's being searched through. If we've
            # reached the bottom (relative to where the user defined it to be),
            # end the search.
            depth -= 1
            if depth == -1:
                return None
        
    def _get_global(self, name, args=None, globs=None):
        "Gets a variable from the predefined variable context."
        
        # Allow overriding of the global entities
        if globs is None:
            globs = GLOBAL_ENTITIES
        
        self._debug("SEEK_GLOBAL>>%s" % name)
        if name not in globs:
            self._debug("SEEK_GLOBAL>>FAILED")
            return None
        
        self._debug("SEEK_GLOBAL>>FOUND>>%s" % name)
        return self._build_global(name, globs[name], args)
    
    def _build_global(self, name, entity, args=None):
        "Builds an object based on an entity from the predefined entity list"
        
        if "dangerous" in entity:
            dang = entity["dangerous"]
            print type(dang), args
            if isinstance(dang, types.LambdaType) and args is not None:
                is_dangerous = dang(*args)
                if is_dangerous:
                    self._debug("DANGEROUS>>VIA LAMBDA")
                    self.err.error(("testcases_javascript_traverser",
                                    "_build_global",
                                    "dangerous_global_called"),
                                   "Dangerous Global Called",
                                   ["""A dangerous global function was called
                                    by some JavaScript code.""",
                                    "Dangerous function: %s" % name],
                                   self.filename,
                                   self.line)
            elif dang:
                self._debug("DANGEROUS")
                self.err.error(("testcases_javascript_traverser",
                                "_build_global",
                                "dangerous_global"),
                               "Dangerous Global Object",
                               ["""A dangerous or banned global object was
                                accessed by some JavaScript code.""",
                                "Accessed object: %s" % name],
                               self.filename,
                               self.line)
    
    def _set_variable(self, name, value, glob=False):
        "Sets the value of a variable/object in the local or global scope."
        
        self._debug("SETTING_OBJECT")
        
        for i in range(len(self.contexts) - 1, 0):
            context = self.contexts[i]
            if name in context:
                context.set(name, value)
                return value
        
        if name in GLOBAL_ENTITIES:
            # TODO : In the future, this should account for non-readonly
            # entities (i.e.: localStorage)
            self._debug("GLOBAL_OVERWRITE")
            self.err.error(("testcases_javascript_traverser",
                            "_set_variable",
                            "global_overwrite"),
                            "Global Overwrite",
                            ["A local variable was created that overwrites "
                             "an object in the global scope.",
                             "Entity name: %s" % name],
                            self.filename,
                            self.line)
            return None

        self.contexts[0 if glob else -1].set(name, value)
        return value
    

class JSContext(object):
    "A variable context"
    
    def __init__(self, context_type):
        self._type = context_type
        self.data = {}
    
    def get(self, name):
        return self.data[name] if name in self.data else None
    
    def set(self, name, variable):
        self.data[name] = variable
    
    def has_var(self, name):
        return name in self.data

    def output(self):
        output = {}
        for (name, item) in self.data.items():
            output[name] = relish(item)
        return json.dumps(output)

class JSWrapper(object):
    "Wraps a JS value and handles contextual functions for it."

    def __init__(self, name, const=False, dirty=False, lazy=False):
        self.name = name
        self.const = const
        self.dirty = False
        self.is_global = False

        self.value = None
        self.lazy = lazy

    def set_value(self, traverser, value, overwrite_const=False):
        if self.const and not overwrite_const:
            traverser.err.error(("testcases_javascript_traverser",
                                 "JSWrapper_set_value",
                                 "const_overwrite"),
                                "Overwritten constant value",
                                ["A variable declared as constant has been "
                                 "overwritten in some JS code.",
                                 "Constant name: %s" % self.name],
                                traverser.filename,
                                traverser.line)

        if value is bool or \
           value is str or \
           value is int or \
           value is float:
            value = JSLiteral(value)
        # If the value being assigned is a wrapper as well, copy it in
        elif value is JSWrapper:
            self.value = value.value
            self.lazy = value.lazy
            self.dirty = True # This may not be necessary
            self.is_global = value.is_global
            # const does not carry over on reassignment
            return self

        self.value = value
        return self
    
    def set_value_from_expression(self, traverser, node):
        "Sets the value of the variable from a node object"
        
        self.set_value(traverser._traverse_node(node))

    def set_value_as_lambda(self, traverser, node):
        "Sets the value of the variable to that of a callable object"
        pass

    def has_property(self, property):
        """Returns a boolean value representing the presence of a property"""
        
        if self.value is None:
            return False
        
        if self.value is JSLiteral:
            return False
        elif self.value is JSObject or \
             self.value is JSPrototype:
            # JSPrototype and JSObject always has a value
            return True

    def get(self, traverser, name):
        "Retrieves a property from the variable"

        if self.value is None:
            return None

        if self.value is JSLiteral:
            return None # This might need tweaking for properties
        elif self.value is JSObject or \
             self.value is JSArray:
            output = self.value.get(traverser, name)
        elif self.value is JSPrototype:
            output = self.value.get(name)
        else:
            output = None
        
        wrapper = JSWrapper(name)
        wrapper.set_value(output)
        return wrapper
    
    def is_literal(self):
        "Returns whether the content is a literal"
        return self.value is JSLiteral

    def get_literal_value(self):
        "Returns the literal value of the wrapper"
        if self.value is None:
            return None
        elif self.value is JSLiteral:
            return self.value.value
        else:
            return False # TODO: This needs to be properly implemented

    def output(self):
        "Returns a readable version of the object"

        if self.value is JSLiteral:
            return json.dumps(self.value.value)
        elif self.value is JSPrototype:
            return "<<PROTOTYPE>>"
        elif self.value is JSObject:
            properties = {}
            for (name, property) in self.value.data:
                if property is types.LambdaType:
                    properties[name] = "<<LAMBDA>>"
                    continue
                wrapper = JSWrapper(name)
                wrapper.set_value(property)
                properties[name] = wrapper.output()
            return json.dumps(properties)
        elif self.value is JSArray:
            return None # These aren't implemented yet!

class JSLiteral(object):
    "Represents a literal JavaScript value"
    
    def __init__(self, value=None):
        self.value = value
    
    def set_value(self, value,):
        self.value = value

    def __str__(self):
        "Returns a human-readable version of the variable's contents"
        return json.dumps(self.value)

class JSObject(object):
    """Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements"""
    
    def __init__(self):
        self.data = {
            "prototype": JSPrototype(),
            "constructor": lambda **keys: JSObject(keys["anon"])
        }

    def get(self, name):
        return self.data[name] if name in self.data else None

    def set(self, name, variable):
        self.data[name] = variable
    
class JSPrototype:
    """A lazy JavaScript object that is assumed not to contain any default
    methods"""
    
    def __init__(self):
        self.data = {}
    
    def get(self, name):
        "Enables static analysis of `with` statements"
        if name == "prototype":
            return JSPrototype()
        elif name not in self.data:
            return None
        else:
            return self.data[name]
    
    def set(self, name, variable):
        "Helpful for `with` statements"
        self.data[name] = variable
    
    def has_var(self, name):
        return name in self.data

    def __str__(self):
        return "<<PROTOTYPE>>"

    def output(self):
        "Simply an alias for __str__"
        return self.__str__()

class JSArray:
    "A class that represents both a JS Array and a JS list."
    
    def __init__(self):
        self.elements = []
    
    def get(self, index):
        return self.elements[index]
