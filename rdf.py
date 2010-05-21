import sys

import rdflib
from rdflib.graph import Graph
from rdflib import URIRef
from cStringIO import StringIO

class RDFTester:
    """This little gem (not to be confused with a Ruby gem) loads and
    parses an RDF file."""
    
    def __init__(self, data):
        """Open a file, attempt to parse it.
        
        If we can parse the file, return the structure; otherwise None"""
        
        # Load up and parse the file in XML format.
        rdfGraph = Graph()
        
        # Try it!
        pseudo_file = StringIO(data) # Wrap data in a pseudo-file
        rdfGraph.parse(pseudo_file, format="xml")
            
            # TODO: Whatever else is involved in parsing. We need to pull
            # out all of the fun and delicious things that we're going to
            # need for the rest of the application and put them into a
            # dictionary. Because we're cool.
        
        self.rdf = rdfGraph
    