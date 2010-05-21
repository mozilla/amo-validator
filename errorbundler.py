
class ErrorBundle:
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
        self.detected_type = 0
        self.resources = {}
        
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
        
    def set_type(self, type):
        "Stores the type of addon we're scanning"
        self.detected_type = type
    
    def failed(self):
        """Returns a boolean value describing whether the validation
        succeeded or not."""
        
        return self.errors or self.warnings
        
    def get_resource(self, name):
        "Retrieves an object that has been stored by another test."
        
        return self.resources[name]
        
    def save_resource(self, name, resource):
        "Saves an object such that it can be used by other tests."
        
        self.resources[name] = resource
        
    def print_summary(self):
        "Prints a summary of the validation process so far."
        
        # This is a reverse translation of the various types to their
        # human-friendly names.
        types = {0: "Unknown",
                 1: "Extension/Multi-Extension",
                 2: "Theme",
                 3: "Dictionary",
                 4: "Language Pack",
                 5: "Search Provider"}
        
        # Make a neat little printout.
        print "Summary:"
        print "-" * 30
        print "Detected type: %s" % types[self.detected_type]
        print "-" * 30
        
        if self.failed():
            print "Test failed! Errors:"
            
            # Print out all the errors:
            for error in self.errors:
                print "Error: %s" % error["message"]
            for warning in self.warnings:
                print "Warning: %s" % warning["message"]
            
        else:
            print "All tests succeeded!"
        
        