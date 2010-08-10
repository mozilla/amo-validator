
class ChromeManifest(object):
    """This class enables convenient reading and searching of
    chrome.manifest files."""
    
    def __init__(self, data):
        "Reads an ntriples style chrome.manifest file"
        
        self.data = data
        self.lines = data.split("\n")
        
        # Extract the data from the triples in the manifest
        triples = []
        counter = 0
        
        for line in self.lines:
            
            counter += 1
            
            # Skip weird lines.
            if len(line) < 5 or line.startswith("#"):
                continue
            
            triple = line.split(None, 2)
            triple = [singlet.strip() for singlet in triple]
            triples.append({"subject": triple[0],
                            "predicate": triple[1],
                            "object": triple[2],
                            "line": counter})
        
        self.triples = triples
        
    def get_value(self, subject=None, predicate=None, object_=None):
        """Returns the first triple value matching the given subject,
        predicate, and/or object"""
        
        for triple in self.triples:
            
            # Filter out non-matches
            if (subject and triple["subject"] != subject) or \
               (predicate and triple["predicate"] != predicate) or \
               (object_ and triple["object"] != object_):
                continue
            
            # Return the first found.
            return triple
        
        return None
        
    def get_objects(self, subject=None, predicate=None):
        """Returns a generator of objects that correspond to the
        specified subjects and predicates."""
        
        for triple in self.triples:
            
            # Filter out non-matches
            if (subject and triple["subject"] != subject) or \
               (predicate and triple["predicate"] != predicate):
                continue
                
            yield triple["object"]
        
    def get_triples(self, subject=None, predicate=None, object_=None):
        """Returns triples that correspond to the specified subject,
        predicates, and objects."""
        
        for triple in self.triples:
            
            # Filter out non-matches
            if subject is not None and triple["subject"] != subject:
                continue
            if predicate is not None and \
               triple["predicate"] != predicate:
                continue
            if object_ is not None and triple["object"] != object_:
                continue
                
            yield triple
        
        