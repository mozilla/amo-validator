import json
import types

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
            output = value.get(name)
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
        # TODO : Maybe make this more compatible with functions
        return "[object Object]"

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
        if index == "length":
            return len(self.elements)

        # Courtesy of Ian Bicking: http://bit.ly/hxv6qt
        try:
            return self.elements[int(index.strip().split()[0])]
        except (ValueError, IndexError, KeyError):
            return None
    
    def get_literal_value(self):
        "Arrays return a comma-delimited version of themselves"
        # Interestingly enough, this allows for things like:
        # x = [4]
        # y = x * 3 // y = 12 since x equals "4"
        return ",".join([str(w.get_literal_value()) for w in self.elements])

