import sys
import re

import curses
import json

COLORS = ("BLUE", "RED", "GREEN", "YELLOW", "WHITE", "BLACK")


class ErrorBundle:
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical."""
    
    def __init__(self, pipe=None):
        """Specifying pipe allows the output of the bundler to be
        written to a file rather than to the screen."""
        
        self.errors = []
        self.warnings = []
        self.infos = []
        
        self.subpackages = []
        self.package_stack = []
        
        self.detected_type = 0
        self.resources = {}
        self.reject = False
        
        self.pipe = pipe
        
        # Get curses all ready to write some stuff to the screen.
        curses.setupterm()
        
        # Initialize a store for the colors and pre-populate it with
        # the un-color color.
        self.colors = {}
        self.colors["NORMAL"] = curses.tigetstr("sgr0") or ''
        
        # Determines capabilities of the terminal.
        fgColorSeq = curses.tigetstr('setaf') or \
            curses.tigetstr('setf') or ''
        
        # Go through each color and figure out what the sequences are
        # for each, then store the sequences in the store we made
        # above.
        for color in COLORS:
            colorIndex = getattr(curses, 'COLOR_%s' % color)
            self.colors[color] = curses.tparm(fgColorSeq, colorIndex)
            
        
    def error(self, error, description=''):
        "Stores an error message for the validation process"
        self.errors.append({"message": error,
                            "description": description})
        return self
        
    def warning(self, warning, description=''):
        "Stores a warning message for the validation process"
        self.warnings.append({"message": warning,
                              "description": description})
        return self

    def info(self, info, description=''):
        "Stores an informational message about the validation"
        self.infos.append({"message": info,
                              "description": description})
        return self
        
    def set_type(self, type_):
        "Stores the type of addon we're scanning"
        self.detected_type = type_
    
    def failed(self):
        """Returns a boolean value describing whether the validation
        succeeded or not."""
        
        return self.errors or self.warnings
        
    def get_resource(self, name):
        "Retrieves an object that has been stored by another test."
        
        if not name in self.resources:
            return False
        
        return self.resources[name]
        
    def save_resource(self, name, resource):
        "Saves an object such that it can be used by other tests."
        
        self.resources[name] = resource
        
    
    def push_state(self, new_file=""):
        "Saves the current error state to parse subpackages"
        
        self.subpackages.append({"errors": self.errors,
                                 "warnings": self.warnings,
                                 "infos": self.infos,
                                 "detected_type": self.detected_type,
                                 "resources": self.resources})
        
        self.errors = []
        self.warnings = []
        self.infos = []
        self.resources = {}
        
        self.package_stack.append(new_file)
    
    def pop_state(self):
        "Retrieves the last saved state and restores it."
        
        # Save a copy of the current state.
        state = self.subpackages.pop()
        errors = self.errors
        warnings = self.warnings
        infos = self.infos
        
        # Copy the existing state back into place
        self.errors = state["errors"]
        self.warnings = state["warnings"]
        self.infos = state["infos"]
        self.detected_type = state["detected_type"]
        self.resources = state["resources"]
        
        name = self.package_stack.pop()
        
        # Overlay the popped warnings onto the existing ones.
        for error in errors:
            self.error("%s > %s" % (name, error["message"]),
                       error["description"])
        for warning in warnings:
            self.warning("%s > %s" % (name, warning["message"]),
                         warning["description"])
        for info in infos:
            self.info("%s > %s" % (name, info["message"]),
                      info["description"])
        
    
    def print_json(self):
        "Prints a JSON summary of the validation operation."
        
        output = {"detected_type": self.detected_type,
                  "success": not self.failed(),
                  "messages":[]}
        
        messages = output["messages"]
        
        # Copy messages to the JSON output
        for error in self.errors:
            messages.append({"type": "error",
                             "message": error["message"],
                             "description": error["description"]})
        for warning in self.warnings:
            messages.append({"type": "warning",
                             "message": warning["message"],
                             "description": warning["description"]})
        for info in self.warnings:
            messages.append({"type": "info",
                             "message": info["message"],
                             "description": info["description"]})
        
        # Output the JSON.
        json_output = json.dumps(output)
        self.pretty_print(json_output, True)
        
    def colorize_text(self, text):
        """Adds escape sequences to colorize text and make it
        beautiful. To colorize text, prefix the text you want to color
        with the color (capitalized) wrapped in double angle brackets
        (i.e.: <<GREEN>>). End your string with <<NORMAL>>."""
        
        # Take note of where the escape sequences are.
        rnormal = text.rfind("<<NORMAL")
        rany = text.rfind("<<")
        
        # Put in the escape sequences.
        text = text.replace("<<", "%(").replace(">>", ")s")
        
        # Make sure that the last sequence is a NORMAL sequence.
        if rany > -1 and rnormal < rany:
            text += "%(NORMAL)s"
        
        # Replace our placeholders with the physical sequence data.
        return text % self.colors
        
        
    def pretty_print(self, text, no_color=False):
        "Uses curses to print in the fanciest way possible."
        
        # Add color to the terminal.
        if not no_color:
            text = self.colorize_text(text)
        else:
            pattern = re.compile("\<\<[A-Z]*?\>\>")
            text = pattern.sub("", text)
            
        
        text += "\n"
        
        if self.pipe:
            self.pipe.write(text)
        else:
            sys.stdout(text)
        
    
    def print_summary(self, verbose=False, no_color=False):
        "Prints a summary of the validation process so far."
        
        
        
        types = {0: "Unknown",
                 1: "Extension/Multi-Extension",
                 2: "Theme",
                 3: "Dictionary",
                 4: "Language Pack",
                 5: "Search Provider",
                 7: "Subpackage"}
        detected_type = types[self.detected_type]
        
        # Make a neat little printout.
        self.pretty_print("\n<<GREEN>>Summary:", no_color) # Line break!
        self.pretty_print("-" * 30)
        self.pretty_print("Detected type: <<BLUE>>%s" % detected_type, no_color)
        self.pretty_print("-" * 30)
        
        if self.failed():
            self.pretty_print("<<BLUE>>Test failed! Errors:", no_color)
            
            # Print out all the errors:
            for error in self.errors:
                self.pretty_print("<<RED>>Error:<<NORMAL>> %s" % error["message"], no_color)
            for warning in self.warnings:
                self.pretty_print("<<YELLOW>>Warning:<<NORMAL>> %s" % warning["message"], no_color)
            
            self._print_verbose(verbose, no_color)
            
            # Awwww... have some self esteem!
            if self.reject:
                self.pretty_print("Extension Rejected")
            
        else:
            self.pretty_print("<<GREEN>>All tests succeeded!", no_color)
            self._print_verbose(verbose, no_color)
            
        self.pretty_print("\n")
        
    def _print_verbose(self, verbose, no_color):
        "Prints info code to help prevent code duplication"
        
        if self.infos and verbose:
            for info in self.infos:
                self.pretty_print("<<WHITE>>Notice:<<NORMAL>> %s" % info["message"], no_color)
        