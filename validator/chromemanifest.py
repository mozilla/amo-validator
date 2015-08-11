import os.path

from validator.contextgenerator import ContextGenerator


class ChromeManifest(object):
    """This class enables convenient parsing and iteration of
    chrome.manifest files."""

    def __init__(self, data, path):
        self.context = ContextGenerator(data)
        self.lines = data.split('\n')

        # Extract the data from the triples in the manifest
        triples = []
        counter = 0

        for line in self.lines:
            line = line.strip()

            counter += 1

            # Skip weird lines.
            if line.startswith('#'):
                continue

            triple = line.split(None, 2)
            if not triple:
                continue
            elif len(triple) == 2:
                triple.append('')
            if len(triple) < 3:
                continue

            triples.append({'subject': triple[0],
                            'predicate': triple[1],
                            'object': triple[2],
                            'line': counter,
                            'filename': path,
                            'context': self.context})

        self.triples = triples

    def get_value(self, subject=None, predicate=None, object_=None):
        """Returns the first triple value matching the given subject,
        predicate, and/or object"""

        for triple in self.triples:

            # Filter out non-matches
            if (subject and triple['subject'] != subject) or \
               (predicate and triple['predicate'] != predicate) or \
               (object_ and triple['object'] != object_):  # pragma: no cover
                continue

            # Return the first found.
            return triple

        return None

    def get_objects(self, subject=None, predicate=None):
        """Returns a generator of objects that correspond to the
        specified subjects and predicates."""

        for triple in self.triples:

            # Filter out non-matches
            if ((subject and triple['subject'] != subject) or
                (predicate and triple['predicate'] != predicate)):
                continue

            yield triple['object']

    def get_triples(self, subject=None, predicate=None, object_=None):
        """Returns triples that correspond to the specified subject,
        predicates, and objects."""

        for triple in self.triples:

            # Filter out non-matches
            if subject is not None and triple['subject'] != subject:
                continue
            if predicate is not None and triple['predicate'] != predicate:
                continue
            if object_ is not None and triple['object'] != object_:
                continue

            yield triple

    def get_applicable_overlays(self, error_bundle):
        """
        Given an error bundle, a list of overlays that are present in the
        current package or subpackage are returned.
        """

        content_paths = self.get_triples(subject='content')
        if not content_paths:
            return set()

        # Create some variables that will store where the applicable content
        # instruction path references and where it links to.
        chrome_path = ''
        content_root_path = '/'

        # Look through each of the listed packages and paths.
        for path in content_paths:
            chrome_name = path['predicate']
            if not path['object']:
                continue
            path_location = path['object'].strip().split()[0]

            # Handle jarred paths differently.
            if path_location.startswith('jar:'):
                if not error_bundle.is_nested_package:
                    continue

                # Parse out the JAR and it's location within the chrome.
                split_jar_url = path_location[4:].split('!', 2)
                # Ignore invalid/unsupported JAR URLs.
                if len(split_jar_url) != 2:
                    continue

                # Unpack the JAR URL.
                jar_path, package_path = split_jar_url

                # Ignore the instruction if the JAR it points to doesn't match
                # up with the current subpackage tree.
                if jar_path != error_bundle.package_stack[0]:
                    continue
                chrome_path = self._url_chunk_join(chrome_name, package_path)
                # content_root_path stays at the default: /

                break
            else:
                # If we're in a subpackage, a content instruction referring to
                # the root of the package obviously doesn't apply.
                if error_bundle.is_nested_package:
                    continue

                chrome_path = self._url_chunk_join(chrome_name, 'content')
                content_root_path = '/%s/' % path_location.strip('/')
                break

        if not chrome_path:
            return set()

        applicable_overlays = set()
        chrome_path = 'chrome://%s' % self._url_chunk_join(chrome_path + '/')

        for overlay in self.get_triples(subject='overlay'):
            if not overlay['object']:
                error_bundle.error(
                    err_id=('chromemanifest', 'get_applicable_overalys',
                            'object'),
                    error='Overlay instruction missing a property.',
                    description='When overlays are registered in a chrome '
                                'manifest file, they require a namespace and '
                                'a chrome URL at minimum.',
                    filename=overlay['filename'],
                    line=overlay['line'],
                    context=self.context)  #TODO(basta): Update this!
                continue
            overlay_url = overlay['object'].split()[0]
            if overlay_url.startswith(chrome_path):
                overlay_relative_path = overlay_url[len(chrome_path):]
                applicable_overlays.add('/%s' %
                        self._url_chunk_join(content_root_path,
                                             overlay_relative_path))

        return applicable_overlays

    def reverse_lookup(self, state, path):
        """
        Returns a chrome URL for a given path, given the current package depth
        in an error bundle.

        State may either be an error bundle or the actual package stack.
        """

        # Make sure the path starts with a forward slash.
        if not path.startswith('/'):
            path = '/%s' % path

        # If the state is an error bundle, extract the package stack.
        if not isinstance(state, list):
            state = state.package_stack

        content_paths = self.get_triples(subject='content')
        for content_path in content_paths:
            chrome_name = content_path['predicate']
            if not content_path['object']:
                continue
            path_location = content_path['object'].split()[0]

            if path_location.startswith('jar:'):
                if not state:
                    continue

                # Parse out the JAR and it's location within the chrome.
                split_jar_url = path_location[4:].split('!', 2)
                # Ignore invalid/unsupported JAR URLs.
                if len(split_jar_url) != 2:
                    continue

                # Unpack the JAR URL.
                jar_path, package_path = split_jar_url

                if jar_path != state[0]:
                    continue

                return 'chrome://%s' % self._url_chunk_join(chrome_name,
                                                            package_path,
                                                            path)
            else:
                if state:
                    continue

                path_location = '/%s/' % path_location.strip('/')
                rel_path = os.path.relpath(path, path_location)

                if rel_path.startswith('../') or rel_path == '..':
                    continue

                return 'chrome://%s' % self._url_chunk_join(chrome_name,
                                                            rel_path)

        return None

    def _url_chunk_join(self, *args):
        """Join the arguments together to form a predictable URL chunk."""
        # Strip slashes from either side of each path piece.
        pathlets = map(lambda s: s.strip('/'), args)
        # Remove empty pieces.
        pathlets = filter(None, pathlets)
        url = '/'.join(pathlets)
        # If this is a directory, add a trailing slash.
        if args[-1].endswith('/'):
            url = '%s/' % url
        return url

