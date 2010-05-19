import sys

import rdflib
from rdflib.graph import Graph

class RDFTester:
    """This little gem (not to be confused with a Ruby gem) loads and
    parses an RDF file."""
    
    def __init__(file):
        """Open a file, attempt to parse it.
        
        If we can parse the file, return the structure; otherwise None"""
        
        # Load up and parse the file in XML format.
        rdfGraph = Graph()
        
        # Try it!
        try:
            rdfGraph.parse(file, format="xml")
            
            # TODO: Whatever else is involved in parsing. We need to pull
            # out all of the fun and delicious things that we're going to
            # need for the rest of the application and put them into a
            # dictionary. Because we're cool.
            
        except:
            # This signifies that there is a parsing error.
            # We're just going to return None.
            return None
        
        return rdfGraph
    
    

#Run the code above.
rdfDoc = parseRDF(sys.argv[1])
print rdfDoc
