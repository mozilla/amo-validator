import platform
import uuid

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
        self.message_tree = {}
        
        self.metadata = {}
        self.determined = False
        
        self.subpackages = []
        self.package_stack = []
        
        self.detected_type = 0
        self.resources = {}
        self.reject = False
        
        self.handler = OutputHandler(pipe, no_color)
            
        
    def error(self, err_id, error, description='', filename='', line=0):
        "Stores an error message for the validation process"
        self._save_message(self.errors,
                           "errors",
                           {"id": err_id,
                            "message": error,
                            "description": description,
                            "file": filename,
                            "line": line})
        return self
        
    def warning(self, err_id, warning, description='', filename='', line=0):
        "Stores a warning message for the validation process"
        self._save_message(self.warnings,
                           "warnings",
                           {"id": err_id,
                            "message": warning,
                            "description": description,
                            "file": filename,
                            "line": line})
        return self

    def info(self, err_id, info, description='', filename='', line=0):
        "Stores an informational message about the validation"
        self._save_message(self.infos,
                           "infos",
                           {"id": err_id,
                            "message": info,
                            "description": description,
                            "file": filename,
                            "line": line})
        return self
        
    def _save_message(self, stack, type_, message):
        "Stores a message in the appropriate message stack."
        
        uid = uuid.uuid1().hex
        
        message["uid"] = uid
        stack.append(message)
        
        if message["id"]:
            tree = self.message_tree
            last_id = None
            for eid in message["id"]:
                if last_id is not None:
                    tree = tree[last_id]
                if eid not in tree:
                    tree[eid] = {"__errors": 0,
                                 "__warnings": 0,
                                 "__infos": 0,
                                 "__messages": []}
                tree[eid]["__%s" % type_] += 1
                last_id = eid
        
            tree[last_id]['__messages'].append(uid)
        
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
                                 "resources": self.resources,
                                 "message_tree": self.message_tree})
        
        self.errors = []
        self.warnings = []
        self.infos = []
        self.resources = {}
        self.message_tree = {}
        
        self.package_stack.append(new_file)
    
    def pop_state(self):
        "Retrieves the last saved state and restores it."
        
        # Save a copy of the current state.
        state = self.subpackages.pop()
        errors = self.errors
        warnings = self.warnings
        infos = self.infos
        # We only rebuild message_tree anyway. No need to restore.
        
        # Copy the existing state back into place
        self.errors = state["errors"]
        self.warnings = state["warnings"]
        self.infos = state["infos"]
        self.detected_type = state["detected_type"]
        self.resources = state["resources"]
        self.message_tree = state["message_tree"]
        
        name = self.package_stack.pop()
        
        self._merge_messages(errors, self.error, name)
        self._merge_messages(warnings, self.warning, name)
        self._merge_messages(infos, self.info, name)
        
    
    def _merge_messages(self, messages, callback, name):
        "Merges a stack of messages into another stack of messages"
        
        # Overlay the popped warnings onto the existing ones.
        for message in messages:
            trace = [name]
            # If there are sub-sub-packages, they'll be in a list.
            if isinstance(message["file"], list):
                trace.extend(message["file"])
            else:
                trace.append(message["file"])
            
            # Write the errors with the file structure delimited by
            # right carets.
            callback(message["id"],
                     "%s > %s" % (name, message["message"]),
                     message["description"],
                     trace,
                     message["line"])
        
    
    def _clean_description(self, message, json=False):
        "Cleans all the nasty whitespace from the descriptions."
        
        output = self._clean_message(message["description"], json)
        message["description"] = output
        
    def _clean_message(self, desc, json=False):
        "Cleans all the nasty whitespace from a string."
        
        output = []
        
        if not isinstance(desc, list):
            lines = desc.splitlines()
            for line in lines:
                output.append(line.strip())
            return " ".join(output)
        else:
            for line in desc:
                output.append(self._clean_message(line, json))
            if json:
                return output
            else:
                return "\n".join(output)
    
    def print_json(self, cluster=False):
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
                  "infos": len(self.infos),
                  "message_tree": self.message_tree}
        
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
        output = [prefix, self._clean_message([message["message"]])]
        
        # We have some extra stuff for verbose mode.
        if verbose:
            verbose_output = []
            
            # Detailed problem description.
            if message["description"]:
                # These are dirty, so strip out whitespace and concat.
                verbose_output.append(
                            self._clean_message(message["description"]))
            
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
        
        if self.infos and verbose:
            mesg = "<<WHITE>>Notice:<<NORMAL>>\t"
            for info in self.infos:
                self._print_message(mesg, info)
        