import json
import types

from validator.testcases.javascript.nodedefinitions import DEFINITIONS
from validator.testcases.javascript.predefinedentities import GLOBAL_ENTITIES

DEBUG = False

class MockBundler:
    def __init__(self):
        self.message_count = 0
        self.final_context = None
        self.tier = 4

    def get_resource(self, name):
        "Represents a resource store"

        return False

    def error(self, id, title, description, filename="",
              line=1, column=0, context=None):
        "Represents a mock error"
        
        # Increment the message counter
        self.message_count += 1

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
        print "in %s:line %d (%d)" % (file, line, column)

    def warning(self, id, title, description, filename="",
                line=1, column=0, context=None):
        self.error(id, title, description, file, line, column, context)

    def info(self, id, title, description, filename="",
             line=1, column=0, context=None):
        self.error(id, title, description, file, line, column, context)


class Traverser:
    "Traverses the AST Tree and determines problems with a chunk of JS."
    
    def __init__(self, err, filename, start_line=0, context=None):
        if err is not None:
            self.err = err
        else:
            self.err = MockBundler()

        self.contexts = []
        self.block_contexts = []
        self.filename = filename
        self.start_line = start_line
        self.polluted = False
        self.line = 1 # Line number
        self.position = 0 # Column number
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
            print ". " * self.debug_level + output

    def run(self, data):
        if DEBUG:
            x = open("/tmp/output.js", "w")
            x.write(str(data))
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

            # This performs the namespace pollution test.
            # {prefix, count}

            # TODO : Make sure to respect JS modules (Bug 531311)

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
        
        # Handles all the E4X stuff and anything that may or may not return
        # a value.
        if "type" not in node or not self._can_handle_node(node["type"]):
            wrapper = JSWrapper(None, traverser=self)
            wrapper.set_value(JSObject())
            return wrapper
        
        self._debug("TRAVERSE>>%s" % (node["type"]))
        
        if "loc" in node and node["loc"] is not None:
            self.line = self.start_line + int(node["loc"]["start"]["line"])
            self.position = int(node["loc"]["start"]["column"])
        
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
            self._debug("ACTION>>%s (%s)" %
                    ("halt" if action_result else "continue",
                     node["type"]))
        
        if action_result is None:
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
            return JSWrapper(action_result, traverser=self)
    
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
            return JSWrapper(local_variable, traverser=self)

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
                return JSWrapper(context.get(variable), traverser=self)

            # Decrease the level that's being searched through. If we've
            # reached the bottom (relative to where the user defined it to be),
            # end the search.
            depth -= 1
            if depth == -1:
                return JSWrapper(None, traverser=self)
       
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
            return JSWrapper(None, traverser=self)
        
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
                                 ["""A dangerous or banned global object was
                                  accessed by some JavaScript code.""",
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
        
        if name in GLOBAL_ENTITIES:
            # TODO : In the future, this should account for non-readonly
            # entities (i.e.: localStorage)
            self._debug("GLOBAL_OVERWRITE")
            self.err.warning(("testcases_javascript_traverser",
                              "_set_variable",
                              "global_overwrite"),
                             "Global Overwrite",
                             ["A local variable was created that overwrites "
                              "an object in the global scope.",
                              "Entity name: %s" % name],
                             self.filename,
                             line=self.line,
                             column=self.position,
                             context=self.context)
            return None

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
    

class JSContext(object):
    "A variable context"
    
    def __init__(self, context_type):
        self._type = context_type
        self.data = {}
    
    def get(self, name):
        name = str(name)
        return self.data[name] if name in self.data else None
    
    def set(self, name, variable):
        name = str(name)
        self.data[name] = variable
    
    def has_var(self, name):
        name = str(name)
        return name in self.data

    def output(self):
        output = {}
        for (name, item) in self.data.items():
            output[name] = str(item)
        return json.dumps(output)

class JSWrapper(object):
    "Wraps a JS value and handles contextual functions for it."

    def __init__(self, value=None, const=False, dirty=False, lazy=False,
                 is_global=False, traverser=None):

        self.const = const
        self.traverser = traverser
        self.value = None # Instantiate the placeholder value
        self.is_global = False # Not yet......
        
        if value is not None:
            self.set_value(value, overwrite_const=True)
        
        if not self.is_global:
            self.is_global = is_global # Globals are built seperately

        self.dirty = dirty
        self.lazy = lazy

    def set_value(self, value, traverser=None, overwrite_const=False):
        "Assigns a value to the wrapper"

        # Use a global traverser if it's present.
        if traverser is None:
            traverser = self.traverser

        if self.const and not overwrite_const:
            traverser.err.warning(("testcases_javascript_traverser",
                                   "JSWrapper_set_value",
                                   "const_overwrite"),
                                  "Overwritten constant value",
                                  "A variable declared as constant has been "
                                  "overwritten in some JS code.",
                                  traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)
        
        if value == self.value:
            return

        # We want to obey the permissions of global objects
        if self.is_global:
            # TODO : Write in support for "readonly":False
            traverser.err.warning(("testcases_javascript_traverser",
                                   "JSWrapper_set_value",
                                   "global_overwrite"),
                                  "Global overwrite",
                                  "An attempt to overwrite a global varible "
                                  "made in some JS code.",
                                  traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)
            return self



        if isinstance(value, (bool, str, int, float, unicode)):
            value = JSLiteral(value)
        # If the value being assigned is a wrapper as well, copy it in
        elif isinstance(value, JSWrapper):
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
        
        self.set_value(traverser._traverse_node(node),
                       traverser=traverser)

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
            return JSWrapper(traverser=self)

        value = self.value
        if self.is_global:
            if "value" not in value:
                return JSWrapper(None, traverser=self)

            value_val = value["value"]
            if isinstance(value_val, types.LambdaType):
                value_val = value_val()

            if isinstance(value_val, dict):
                if name in value_val:
                    return traverser._build_global(name=name,
                                                   entity=value_val[name])
            else:
                value = value_val


        if value is JSLiteral:
            return None # This will need tweaking for properties
        elif isinstance(value, (JSObject, JSArray)):
            output = value.get(traverser, name)
        elif isinstance(value, JSPrototype):
            output = value.get(name)
        else:
            output = None
        
        return JSWrapper(output, traverser=self)
    
    def is_literal(self):
        "Returns whether the content is a literal"
        return isinstance(self.value, JSLiteral)

    def get_literal_value(self):
        "Returns the literal value of the wrapper"
        
        if self.is_global:
            return None
        if self.value is None:
            return None
        if self.is_global:
            return ""

        return self.value.get_literal_value()

    def output(self):
        "Returns a readable version of the object"
        if isinstance(self.value, JSLiteral):
            return self.value.value
        elif isinstance(self.value, JSPrototype):
            return "<<PROTOTYPE>>"
        elif isinstance(self.value, JSObject):
            properties = {}
            for (name, property) in self.value.data.items():
                if property is types.LambdaType:
                    properties[name] = "<<LAMBDA>>"
                    continue
                wrapper = JSWrapper(property, traverser=self)
                properties[name] = wrapper.output()
            return json.dumps(properties)
        elif isinstance(self.value, JSArray):
            return None # TODO: These aren't implemented yet!

    def __str__(self):
        "Returns a textual version of the object."
        return str(self.get_literal_value())

class JSLiteral(object):
    "Represents a literal JavaScript value"
    
    def __init__(self, value=None):
        self.value = value
    
    def set_value(self, value,):
        self.value = value

    def __str__(self):
        "Returns a human-readable version of the variable's contents"
        return json.dumps(self.value)

    def get_literal_value(self):
        "Returns the literal value of a this literal. Heh."
        return self.value

class JSObject(object):
    """Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements"""
    
    def __init__(self):
        self.data = {
            "prototype": JSPrototype(),
            "constructor": lambda **keys: JSObject(keys["anon"])
        }

    def get(self, name):
        "Returns the value associated with a property name"
        return self.data[name] if name in self.data else None
    
    def get_literal_value(self):
        "Objects evaluate to empty strings"
        return ""

    def set(self, name, variable):
        "Sets the value of a property"
        self.data[name] = variable

    def has_var(self, name):
        return name in self.data

    def output(self):
        return str(self.data)
    
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
    
    def get_literal_value():
        "Same as JSObject; returns an empty string"
        return ""

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
    
    def get_literal_value(self):
        "Arrays return a comma-delimited version of themselves"
        # Interestingly enough, this allows for things like:
        # x = [4]
        # y = x * 3 // y = 12 since x equals "4"
        return ",".join([str(w.get_literal_value()) for w in self.elements])

