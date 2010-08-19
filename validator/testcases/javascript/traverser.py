import json
import types

from validator.testcases.javascript.nodedefinitions import DEFINITIONS
from validator.testcases.javascript.predefinedentities import GLOBAL_ENTITIES

class Traverser:
    "Traverses the AST Tree and determines problems with a chunk of JS."
    
    def __init__(self, err, filename, start_line=0):
        self.err = err
        self.contexts = []
        self.block_contexts = []
        self.filename = filename
        self.start_line = start_line
        self.polluted = False
        self.line = 0
    
    def run(self, data):
        
        if "type" not in data or not self._can_handle_node(data["type"]):
            self.err.error(("testcases_javascript_traverser",
                            "run",
                            "cannot_interpret_js"),
                           "Cannot interpret JavaScript",
                           """Some JavaScript code was found, but could not be
                           interpreted.""",
                           self.filename,
                           self.start_line)
            return None
        
        self._traverse_node(data)
        
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
        
        # Handles all the E4X stuff and anythign that may or may not return
        # a value.
        if "type" not in node or not self._can_handle_node(node["type"]):
            return JSObject()
        
        self.line = self.start_line + int(node["start"]["line"])
        
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
        
        docontinue = None
        if action is not None:
            docontinue = action(self, node)
        
        if docontinue is not None:
            for branch in branches:
                if branch in node:
                    b = node[branch]
                    if isinstance(b, list):
                        self._interpret_block(b)
                    else:
                        self._traverse_node(b)
        
        if establish_context or block_level:
            self._pop_context()
        
        if returns:
            return docontinue
    
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
    
    def _pop_context(self):
        "Adds a variable context to the current interpretation frame"
        # Keep the global scope on the stack.
        if len(self.contexts) == 1:
            return
        self.contexts = self.contexts[:-1]
    
    def _peek_context(self, depth=1):
        """Returns the most recent context. Note that this should NOT be used
        for variable lookups."""
        
        return self.contexts[:0 - depth]
        
    def _seek_variable(self, variable, depth=-1):
        "Returns the value of a variable that has been declared in a context"
        
        for c in range(len(self.contexts) - 1, 0):
            context = self.contexts[c]
            if context.has_var(variable):
                return context[variable]
            depth -= 1
            if depth == -1:
                return None
        
        return self._get_global(self, name)
    
    def _get_global(self, name, args=None, globs=None):
        "Gets a variable from the predefined variable context."
        
        if globs is None:
            globs = GLOBAL_ENTITIES
        
        if name not in globs:
            return None
        
        for ename, entity in predefinedentities.GLOBAL_ENTITIES.items():
            if ename == name:
                return self._build_global(name, entity, args)
                break
    
    def _build_global(self, name, entity, args=None):
        "Builds an object based on an entity from the predefined entity list"
        
        if "dangerous" in entity:
            dang = entity["dangerous"]
            if isinstance(dang, types.LambdaType) and args is not None:
                is_dangerous = dang(*args)
                if is_dangerous:
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
        pass
    

class JSContext:
    "A variable context"
    
    def __init__(self, context_type):
        self.type_ = context_type
    
    def __getattr__(self, name):
        if name not in self.__dict__:
            return None
        else:
            return self.__dict__[name]
    
    def __setattr__(self, name, variable):
        self.__dict__[name] = variable
    
    def has_var(self, name):
        return name in self.__dict__

class JSVariable:
    "Mimics a JS variable and stores analysis data from the code"
    
    def __init__(self, dirty=False):
        self.value = None
        self.dirty = dirty
        self.const = False
    
    def set_value(self, traverser, value, line=0):
        if self.const:
            traverser.err.error(("testcases_javascript_traverser",
                                 "set_value",
                                 "const_assignment"),
                                "JS Constant re-assigned",
                                """JavaScript constants (const) should not
                                have their value re-assigned after they have
                                been initialized.""",
                                traverser.filename,
                                traverser.line)
        self.value = value

class JSObject:
    """Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements"""
    
    def __init__(self, anonymous=False):
        self.__dict__["prototype"] = JSPrototype()
        self.__dict__["constructor"] = lambda **keys: JSObject(keys["anon"])
        # An anonymous object doesn't complain when bits of it are accessed,
        # even if those bits don't exist.
        self.anon = anonymous
    
    def __getattr__(self, name):
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
