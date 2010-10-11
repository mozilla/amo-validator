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
        print description
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
            print ". " * self.debug_level + str(data)

    def run(self, data):
        
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
            return JSObject()
        
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
            return action_result
    
    def _interpret_block(self, items):
        "Interprets a block of consecutive code"
        
        for item in items:
            self._traverse_node(item)
    
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
        self._debug(popped_context.__dict__)
    
    def _peek_context(self, depth=1):
        """Returns the most recent context. Note that this should NOT be used
        for variable lookups."""
        
        return self.contexts[:0 - depth]
        
    def _seek_variable(self, variable, depth=-1):
        "Returns the value of a variable that has been declared in a context"
        
        self._debug("SEEK>>%s>>%d" % (variable, depth))

        for c in range(len(self.contexts) - 1, 0):
            context = self.contexts[c]
            if context.has_var(variable):
                self._debug("SEEK>>FOUND AT DEPTH %d" % c)
                return context[variable]
            depth -= 1
            if depth == -1:
                return None
        
        self._debug("SEEK_FAIL>>TRYING GLOBAL")
        return self._get_global(variable)
    
    def _get_global(self, name, args=None, globs=None):
        "Gets a variable from the predefined variable context."
        
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
        self.contexts[0 if glob else -1][name] = value
    

class JSContext(object):
    "A variable context"
    
    def __init__(self, context_type):
        self._type = context_type
    
    def __getattr__(self, name):
        if name in ("_type", ):
            return object.__getattr__(self, name)
        
        if name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]
    
    def __setattr__(self, name, variable):
        self.__dict__[name] = variable
    
    def has_var(self, name):
        return name in self.__dict__

class JSVariable(object):
    "Mimics a JS variable and stores analysis data from the code"
    
    def __init__(self, dirty=False):
        self.value = None
        self.dirty = dirty
        self.const = False
    
    def set_value(self, traverser, value, line=0):
        if self.const:
            self._debug("LITERAL>>CONSTANT REASSIGNMENT")
            traverser.err.error(("testcases_javascript_traverser",
                                 "set_value",
                                 "const_assignment"),
                                "JS Constant re-assigned",
                                """JavaScript constants (const) should not
                                have their value re-assigned after they have
                                been initialized.""",
                                traverser.filename,
                                traverser.line)
        traverser._debug("LITERAL::%s" % json.dumps(value))
        self.value = value

    def __str__(self):
        "Returns a human-readable version of the variable's contents"
        return "%s%s" % (("const:" if self.const else ""),
                         json.dumps(self.value))

class JSObject(object):
    """Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements"""
    
    def __init__(self, anonymous=False):
        self.__dict__["prototype"] = JSPrototype()
        self.__dict__["constructor"] = lambda **keys: JSObject(keys["anon"])
        # An anonymous object doesn't complain when bits of it are accessed,
        # even if those bits don't exist.
        self.anon = anonymous
    
    def __getattr__(self, name):
        if name in ("anon", "has_var"):
            return object.__getattr__(self, name)
        
        "Enables static analysis of `with` statements"
        if name not in self.__dict__:
            if self.anon:
                return JSObject(True)
            else:
                return None
        else:
            obj = self.__dict__[name]
            if isinstance(obj, types.LambdaType):
                obj = obj(anon=True)
            return obj
    
    def __setattr__(self, name, variable):
        "Helpful for `with` statements"
        self.__dict__[name] = variable
    
    def has_var(self, name):
        return name in self.__dict__

class JSPrototype:
    """A lazy JavaScript object that is assumed not to contain any default
    methods"""
    
    def __init__(self):
        pass
    
    def __getattr__(self, name):
        "Enables static analysis of `with` statements"
        if name == "prototype":
            return JSPrototype() 
        elif name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]
    
    def __setattr__(self, name, variable):
        "Helpful for `with` statements"
        self.__dict__[name] = variable
    
    def has_var(self, name):
        return name in self.__dict__

class JSArray:
    "A class that represents both a JS Array and a JS list."
    
    def __init__(self):
        self.elements = []
    
    def get(self, index):
        return self.elements[index]
    
