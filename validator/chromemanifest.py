from validator.contextgenerator import ContextGenerator


class ChromeManifest(object):
    """This class enables convenient reading and searching of
    chrome.manifest files."""

    def __init__(self, data, path):
        "Reads an ntriples style chrome.manifest file"

        self.context = ContextGenerator(data)
        self.lines = data.split("\n")

        # Extract the data from the triples in the manifest
        triples = []
        counter = 0

        for line in self.lines:

            counter += 1

            # Skip weird lines.
            if line.startswith("#"):
                continue

            triple = line.split(None, 2)
            if not triple:
                continue
            elif len(triple) == 2:
                triple.append("")
            if len(triple) < 3:
                continue

            triples.append({"subject": triple[0],
                            "predicate": triple[1],
                            "object": triple[2],
                            "line": counter,
                            "filename": path})

        self.triples = triples

    def get_value(self, subject=None, predicate=None, object_=None):
        """Returns the first triple value matching the given subject,
        predicate, and/or object"""

        for triple in self.triples:

            # Filter out non-matches
            if (subject and triple["subject"] != subject) or \
               (predicate and triple["predicate"] != predicate) or \
               (object_ and triple["object"] != object_):  # pragma: no cover
                continue

            # Return the first found.
            return triple

        return None

    def get_objects(self, subject=None, predicate=None):
        """Returns a generator of objects that correspond to the
        specified subjects and predicates."""

        for triple in self.triples:

            # Filter out non-matches
            if (subject and
                triple["subject"] != subject) or \
               (predicate and
                triple["predicate"] != predicate):  # pragma: no cover
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

