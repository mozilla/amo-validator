import sys

import curses
import json

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
        
        self.detected_type = 0
        self.resources = {}
        self.reject = False
        
        self.pipe = pipe
        
        curses.setupterm()
        
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
        
        # Output the JSON
        json_output = json.dumps(output)
        self.pretty_print(json_output)
        
    def colorize_text(self, text, color):
        "Adds escape sequences to colorize text and make it beautiful."
        
        
    def pretty_print(self, text):
        "Uses curses to print in the fanciest way possible."
        
        text += "\n"
        
        if self.pipe:
            self.pipe.write(text)
        else:
            sys.stdout(text)
        
    
    def print_summary(self, verbose=False):
        "Prints a summary of the validation process so far."
        
        types = {0: "Unknown",
                 1: "Extension/Multi-Extension",
                 2: "Theme",
                 3: "Dictionary",
                 4: "Language Pack",
                 5: "Search Provider"}
        detected_type = types[self.detected_type]
        
        # Make a neat little printout.
        self.pretty_print("Summary:")
        self.pretty_print("-" * 30)
        self.pretty_print("Detected type: %s" % detected_type)
        self.pretty_print("-" * 30)
        
        if self.failed():
            self.pretty_print("Test failed! Errors:")
            
            # Print out all the errors:
            for error in self.errors:
                self.pretty_print("Error: %s" % error["message"])
            for warning in self.warnings:
                self.pretty_print("Warning: %s" % warning["message"])
            
            self._print_verbose(verbose)
            
            # Awwww... have some self esteem!
            if self.reject:
                self.pretty_print("Extension Rejected")
            
        else:
            print "All tests succeeded!"
            self._print_verbose(verbose)
        
    def _print_verbose(self, verbose):
        "Prints info code to help prevent code duplication"
        
        if self.infos and verbose:
            for info in self.infos:
                self.pretty_print("Notice: %s" % info["message"])
        