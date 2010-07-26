import platform

import json

if platform.system() != "Windows":
    from outputhandlers.shellcolors import OutputHandler
else: # pragma: no cover
    from outputhandlers.windowscolors import OutputHandler

class ErrorBundle(object):
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
            
        
    def error(self, error, description='', filename='', line=0):
        "Stores an error message for the validation process"
        self.errors.append({"message": error,
                            "description": description,
                            "file": filename,
                            "line": line})
        return self
        
    def warning(self, warning, description='', filename='', line=0):
        "Stores a warning message for the validation process"
        self.warnings.append({"message": warning,
                              "description": description,
                              "file": filename,
                              "line": line})
        return self

    def info(self, info, description='', filename='', line=0):
        "Stores an informational message about the validation"
        self.infos.append({"message": info,
                           "description": description,
                           "file": filename,
                           "line": line})
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
        
    
    def is_nested_package(self):
        "Returns whether the current package is within a PACKAGE_MULTI"
        
        return bool(self.package_stack)
    
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
            trace = [name]
            
            # If there are sub-sub-packages, they'll be in a list.
            if type(error["file"]) is list:
                trace.extend(error["file"])
            else:
                trace.append(error["file"])
            
            # Write the errors with the file structure delimited by
            # right carets.
            self.error("%s > %s" % (name, error["message"]),
                       error["description"],
                       trace,
                       error["line"])
                       
        for warning in warnings:
            trace = [name]
            if type(warning["file"]) is list:
                trace.extend(warning["file"])
            else:
                trace.append(warning["file"])
            
            self.warning("%s > %s" % (name, warning["message"]),
                         warning["description"],
                         trace,
                         warning["line"])
        for info in infos:
            trace = [name]
            if type(info["file"]) is list:
                trace.extend(info["file"])
            else:
                trace.append(info["file"])
            
            self.info("%s > %s" % (name, info["message"]),
                      info["description"],
                      trace,
                      info["line"])
        
    
    def _clean_description(self, message, json=False):
        "Cleans all the nasty whitespace from the descriptions."
        
        if not isinstance(message["description"], list):
            desc = message["description"].split("\n")
        
        output = []
        merge = []
        # Loop through each item in the multipart description.
        for line in desc:
            # If it's a string, add it to the line buffer for concat.
            if isinstance(line, str):
                merge.append(line.strip())
            # If it's a list, just append it.
            elif isinstance(line, list):
                # While you're in here, concat and flush the line buffer.
                if merge:
                    output.append(" ".join(merge))
                
                # JSON keeps the structure, plain text normalizes.
                if json:
                    output.append(line)
                else:
                    output.append(" ".join(line))
        # Finish up the line buffer.
        if merge:
            output.append(" ".join(merge))
    
    def print_json(self):
        "Prints a JSON summary of the validation operation."
        
        types = {0: "unknown",
                 1: "extension",
                 2: "theme",
                 3: "dictionary",
                 4: "langpack",
                 5: "search"}
        output = {"detected_type": types[self.detected_type],
                  "success": not self.failed(),
                  "rejected": self.reject,
                  "messages":[],
                  "errors": len(self.errors),
                  "warnings": len(self.warnings),
                  "infos": len(self.infos)}
        
        messages = output["messages"]
        
        # Copy messages to the JSON output
        for error in self.errors:
            error["type"] = "error"
            self._clean_description(error, True)
            messages.append(error)
            
        for warning in self.warnings:
            warning["type"] = "warning"
            self._clean_description(warning, True)
            messages.append(warning)
            
        for info in self.infos:
            info["type"] = "info"
            self._clean_description(info, True)
            messages.append(info)
        
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
            
            # Print out all the errors/warnings:
            for error in self.errors:
                self._print_message("<<RED>>Error:<<NORMAL>>\t", error, verbose)
            for warning in self.warnings:
                self._print_message("<<YELLOW>>Warning:<<NORMAL>> ", warning, verbose)
            
            # Prints things that only happen during verbose (infos).
            self._print_verbose(verbose)
            
            # Awwww... have some self esteem!
            if self.reject:
                self.handler.write("Extension Rejected")
            
        else:
            self.handler.write("<<GREEN>>All tests succeeded!")
            self._print_verbose(verbose)
            
        self.handler.write("\n")
        
    def _print_message(self, prefix, message, verbose=True):
        "Prints a message and takes care of all sorts of nasty code"
        
        # Load up the standard output.
        output = [prefix,
                  message["message"]]
        
        # We have some extra stuff for verbose mode.
        if verbose:
            verbose_output = []
            
            # Detailed problem description.
            if message["description"]:
                # These are dirty, so strip out whitespace and concat.
                self._clean_description(message)
                verbose_output.append(message["description"])
            
            # If file information is availe, output that as well.
            files = message["file"]
            if files is not None and files != "":
                fmsg = "\tFile:\t%s"
                
                # Nested files (subpackes) are stored in a list.
                if type(files) is list:
                    if files[-1] == "":
                        files[-1] = "(none)"
                    verbose_output.append(fmsg % ' > '.join(files))
                else:
                    verbose_output.append(fmsg % files)
            
            # If there is a line number, that gets put on the end.
            if message["line"]:
                verbose_output.append("\tLine:\t%s" % message["line"])
                
            # Stick it in with the standard items.
            output.append("\n\t")
            output.append("\n\t".join(verbose_output))
        
        # Send the final output to the handler to be rendered.
        self.handler.write(''.join(output))
        
        
    def _print_verbose(self, verbose):
        "Prints info code to help prevent code duplication"
        
        mesg = "<<WHITE>>Notice:<<NORMAL>>\t"
        if self.infos and verbose:
            for info in self.infos:
                self._print_message(mesg, info)
        