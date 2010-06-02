import platform

import json

if platform.system() != "Windows":
    from outputhandlers.shellcolors import OutputHandler
else:
    from outputhandlers.windowscolors import OutputHandler

class ErrorBundle:
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical."""
    
    def __init__(self, pipe=None, no_color=False):
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
        
        self.handler = OutputHandler(pipe, no_color)
            
        
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
        self.handler.write(json_output)
    
    def print_summary(self, verbose=False):
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
        self.handler.write("\n<<GREEN>>Summary:") \
            .write("-" * 30) \
            .write("Detected type: <<BLUE>>%s" % detected_type) \
            .write("-" * 30)
        
        if self.failed():
            self.handler.write("<<BLUE>>Test failed! Errors:")
            
            # Print out all the errors:
            for error in self.errors:
                self.handler.write("<<RED>>Error:<<NORMAL>> %s" % error["message"])
            for warning in self.warnings:
                self.handler.write("<<YELLOW>>Warning:<<NORMAL>> %s" % warning["message"])
            
            self._print_verbose(verbose)
            
            # Awwww... have some self esteem!
            if self.reject:
                self.handler.write("Extension Rejected")
            
        else:
            self.handler.write("<<GREEN>>All tests succeeded!")
            self._print_verbose(verbose)
            
        self.handler.write("\n")
        
    def _print_verbose(self, verbose):
        "Prints info code to help prevent code duplication"
        
        mesg = "<<WHITE>>Notice:<<NORMAL>> %s"
        if self.infos and verbose:
            for info in self.infos:
                self.handler.write(mesg % info["message"])
        