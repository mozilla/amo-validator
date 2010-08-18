
from validator.testcases.javascript.nodedefinitions import DEFINITIONS

class Traverser:
    "Traverses the AST Tree and determines problems with a chunk of JS."
    
    def __init__(self, err, filename, start_line=0):
        self.err = err
        self.contexts = []
        self.filename = filename
        self.start_line = start_line
        self.polluted = False
    
    def run(self, data):
        
        if not self._can_handle_node(data.type):
            self.err.error(("testcases_javascript_traverser",
                            "run",
                            "cannot_interpret_js"),
                           "Cannot interpret JavaScript",
                           """Some JavaScript code was found, but could not be
                           interpreted.""",
                           self.filename)
            return None
        
        self._traverse_node(data)
        
        if self.contexts:
            # This performs the namespace pollution test.
            # {prefix, count}
            prefixes = []
            global_ns = self.contexts[0]
            for name in global_ns.keys():
                
            
        
    
    def _can_handle_node(self, node_name):
        "Determines whether a node can be handled."
        return node_name in DEFINITIONS
    
    def _traverse_node(self, node):
        "Finds a node's internal blocks and helps manage state."
        
        (branches,
         explicitly_dynamic,
         estab_context,
         action) = DEFINITIONS[node.type]
        
        if estab_context:
            self._push_context()
        
        if action is not None:
            action(self, node)
        
        for branch in branches:
            if branch in node:
                b = node[branch]
                if isinstance(b, list):
                    self._interpret_block(b)
                else:
                    if establ_context:
                        self._push_context()
                    
                    self._traverse_node(b)
                    
                    if establ_context:
                        self._pop_context()
        
        if estab_context:
            self._pop_context()
    
    def _push_context(self, default=None):
        "Adds a variable context to the current interpretation frame"
        if default is None:
            default = []
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
        
        return self.contexts[:-1 - depth]
        
    def _seek_variable(self, variable, depth=-1):
        "Returns the value of a variable that has been declared in a context"
        
        for c in range(len(self.contexts) - 1, 0):
            context = self.contexts[c]
            if variable in context:
                return context[variable]
            depth -= 1
            if depth == -1:
                return None
        
        # TODO : At this point, the function should seek out interpreter-
        # defined objects.
        
        return None
    
    def _set_global(self, variable, value, type="string"):
        
    
    def _interpret_block(self, items):
        "Interprets a block of consecutive code"
        
        for item in items:
            self._traverse_node(item)


class JSVariable:
    "Mimics a JS variable and stores analysis data from the code"
    
    def __init__(self):
        self.type = "string"
        self.value = None
        self.dynamic = False
        self.const = False
    
    def set_value(self, value, type="string"):
        if self.const:
            self.err.error(("testcases_javascript_traverser",
                            "set_value",
                            "const_assignment"))
        self.value = value

class JSObject:
    """Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements"""
    
    def __init__(self):
        self.variables = {"prototype": JSPrototype()}
    
    def __getattr__(self, name):
        "Enables static analysis of `with` statements"
        if name not in self.variables:
            return None
        else:
            return self.variables[name]
    
    def __setattr__(self, name, variable):
        "Helpful for `with` statements"
        self.variables[name] = variable

class JSPrototype:
    """A lazy JavaScript object that is assumed not to contain any default
    methods"""
    
    def __init__(self):
        self.variables = {}
    
    def __getattr__(self, name):
        "Enables static analysis of `with` statements"
        if name == "prototype":
            return JSPrototype() 
        elif name not in self.variables:
            return None
        else:
            return self.variables[name]
    
    def __setattr__(self, name, variable):
        "Helpful for `with` statements"
        self.variables[name] = variable
