import json
import sys
import types
import uuid
from functools import partial
from StringIO import StringIO

from outputhandlers.shellcolors import OutputHandler
import unicodehelper


class ErrorBundle(object):
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical.

    Keyword Arguments

    **determined**
        Whether the validator should continue after a tier fails
    **listed**
        True if the add-on is destined for AMO, false if not
    **instant**
        Who knows what this does
    **overrides**
        dict of install.rdf values to override. Possible keys:
        targetapp_minVersion, targetapp_maxVersion
    **spidermonkey**
        Optional path to the local spidermonkey installation
    **for_appversions**
        A dict of app GUIDs referencing lists of versions. Determines which
        version-dependant tests should be run.
    """

    def __init__(self, determined=True, listed=True, instant=False,
                 overrides=None, spidermonkey=False, for_appversions=None):

        self.handler = None

        self.errors = []
        self.warnings = []
        self.notices = []
        self.message_tree = {}

        self.compat_summary = {"errors": 0,
                               "warnings": 0,
                               "notices": 0}

        self.ending_tier = 1
        self.tier = 1

        self.subpackages = []
        self.package_stack = []

        self.detected_type = 0
        self.unfinished = False

        # TODO: Break off into resource helper
        self.resources = {}
        self.pushable_resources = {}
        self.final_context = None

        self.metadata = {'requires_chrome': False}
        if listed:
            self.resources["listed"] = True
        self.instant = instant
        self.determined = determined

        self.version_requirements = None

        self.overrides = overrides or None
        self.save_resource("SPIDERMONKEY", spidermonkey or False)

        self.supported_versions = self.for_appversions = for_appversions

    def _message(type_, message_type):
        def wrap(self, *args, **kwargs):
            message = {
                "id": kwargs.get("err_id") or args[0],
                "message": kwargs.get(message_type) or args[1],
                "description": kwargs.get("description",
                                          args[2] if len(args) > 2 else None),
                # Filename is never None.
                "file": kwargs.get("filename",
                                   args[3] if len(args) > 3 else ""),
                "line": kwargs.get("line",
                                   args[4] if len(args) > 4 else None),
                "column": kwargs.get("column",
                                     args[5] if len(args) > 5 else None),
                # If true, the message should only be shown to editors.
                "editors_only": kwargs.get("editors_only", False),
            }
            for field in ("tier", "for_appversions", "compatibility_type", ):
                message[field] = kwargs.get(field)

            self._save_message(getattr(self, type_), type_, message,
                               context=kwargs.get("context"))
            return self

        wrap.__name__ = message_type
        return wrap

    # And then all the real functions. Ahh, how clean!
    error = _message("errors", "error")
    warning = _message("warnings", "warning")
    notice = _message("notices", "notice")

    def set_tier(self, tier):
        "Updates the tier and ending tier"
        self.tier = tier
        if tier > self.ending_tier:
            self.ending_tier = tier

    @property
    def message_count(self):
        return len(self.errors) + len(self.warnings) + len(self.notices)

    def _save_message(self, stack, type_, message, context=None):
        "Stores a message in the appropriate message stack."

        uid = uuid.uuid4().hex
        message["uid"] = uid

        # Get the context for the message (if there's a context available)
        if context is not None:
            if isinstance(context, tuple):
                message["context"] = context
            else:
                message["context"] = (
                    context.get_context(line=message["line"],
                                        column=message["column"]))
        else:
            message["context"] = None

        message["message"] = unicodehelper.decode(message["message"])
        message["description"] = unicodehelper.decode(message["description"])

        # Test that if for_appversions is set that we're only applying to
        # supported add-ons. THIS IS THE LAST FILTER BEFORE THE MESSAGE IS
        # ADDED TO THE STACK!
        if message["for_appversions"]:
            if not self.supports_version(message["for_appversions"]):
                if self.instant:
                    print "(Instant error discarded)"
                    self._print_message(type_, message, verbose=True)
                return
        elif self.version_requirements:
            # If there was no for_appversions but there were version
            # requirements detailed in the decorator, use the ones from the
            # decorator.
            message["for_appversions"] = self.version_requirements

        # Save the message to the stack.
        stack.append(message)

        # Mark the tier that the error occurred at.
        if message["tier"] is None:
            message["tier"] = self.tier

        # Build out the compatibility summary if possible.
        if message["compatibility_type"]:
            self.compat_summary["%ss" % message["compatibility_type"]] += 1

        # Build out the message tree entry.
        if message["id"]:
            tree = self.message_tree
            last_id = None
            for eid in message["id"]:
                if last_id is not None:
                    tree = tree[last_id]
                if eid not in tree:
                    tree[eid] = {"__errors": 0,
                                 "__warnings": 0,
                                 "__notices": 0,
                                 "__messages": []}
                tree[eid]["__%s" % type_] += 1
                last_id = eid

            tree[last_id]['__messages'].append(uid)

        # If instant mode is turned on, output the message immediately.
        if self.instant:
            self._print_message(type_, message, verbose=True)

    def failed(self, fail_on_warnings=True):
        """Returns a boolean value describing whether the validation
        succeeded or not."""

        return bool(self.errors) or (fail_on_warnings and bool(self.warnings))

    def get_resource(self, name):
        "Retrieves an object that has been stored by another test."

        if name in self.resources:
            return self.resources[name]
        elif name in self.pushable_resources:
            return self.pushable_resources[name]
        else:
            return False

    def save_resource(self, name, resource, pushable=False):
        "Saves an object such that it can be used by other tests."

        if pushable:
            self.pushable_resources[name] = resource
        else:
            self.resources[name] = resource

    @property
    def is_nested_package(self):
        "Returns whether the current package is within a PACKAGE_MULTI"
        return bool(self.package_stack)

    def push_state(self, new_file=""):
        "Saves the current error state to parse subpackages"

        self.subpackages.append({"errors": self.errors,
                                 "warnings": self.warnings,
                                 "notices": self.notices,
                                 "detected_type": self.detected_type,
                                 "message_tree": self.message_tree,
                                 "resources": self.pushable_resources,
                                 "metadata": self.metadata})

        self.errors = []
        self.warnings = []
        self.notices = []
        self.message_tree = {}
        self.pushable_resources = {}
        self.metadata = {'requires_chrome': False}

        self.package_stack.append(new_file)

    def pop_state(self):
        "Retrieves the last saved state and restores it."

        # Save a copy of the current state.
        state = self.subpackages.pop()
        errors = self.errors
        warnings = self.warnings
        notices = self.notices
        metadata = self.metadata
        # We only rebuild message_tree anyway. No need to restore.

        # Copy the existing state back into place
        self.errors = state["errors"]
        self.warnings = state["warnings"]
        self.notices = state["notices"]
        self.detected_type = state["detected_type"]
        self.message_tree = state["message_tree"]
        self.pushable_resources = state["resources"]
        self.metadata = state["metadata"]

        name = self.package_stack.pop()

        self._merge_messages(errors, self.error, name)
        self._merge_messages(warnings, self.warning, name)
        self._merge_messages(notices, self.notice, name)

        self.metadata.setdefault("sub_packages", {})[name] = metadata

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
                     message["message"],
                     description=message["description"],
                     filename=trace,
                     line=message["line"],
                     column=message["column"],
                     context=message["context"],
                     tier=message["tier"],
                     for_appversions=message["for_appversions"],
                     compatibility_type=message["compatibility_type"])

    def render_json(self):
        "Returns a JSON summary of the validation operation."

        types = {0: "unknown",
                 1: "extension",
                 2: "theme",
                 3: "dictionary",
                 4: "langpack",
                 5: "search",
                 8: "webapp"}
        output = {"detected_type": types[self.detected_type],
                  "ending_tier": self.ending_tier,
                  "success": not self.failed(),
                  "messages": [],
                  "errors": len(self.errors),
                  "warnings": len(self.warnings),
                  "notices": len(self.notices),
                  "message_tree": self.message_tree,
                  "compatibility_summary": self.compat_summary,
                  "metadata": self.metadata}

        messages = output["messages"]

        # Copy messages to the JSON output
        for error in self.errors:
            error["type"] = "error"
            messages.append(error)

        for warning in self.warnings:
            warning["type"] = "warning"
            messages.append(warning)

        for notice in self.notices:
            notice["type"] = "notice"
            messages.append(notice)

        # Output the JSON.
        return json.dumps(output)

    def print_summary(self, verbose=False, no_color=False):
        "Prints a summary of the validation process so far."

        types = {0: "Unknown",
                 1: "Extension/Multi-Extension",
                 2: "Full Theme",
                 3: "Dictionary",
                 4: "Language Pack",
                 5: "Search Provider",
                 7: "Subpackage",
                 8: "App"}
        detected_type = types[self.detected_type]

        buffer = StringIO()
        self.handler = OutputHandler(buffer, no_color)

        # Make a neat little printout.
        self.handler.write("\n<<GREEN>>Summary:") \
            .write("-" * 30) \
            .write("Detected type: <<BLUE>>%s" % detected_type) \
            .write("-" * 30)

        if self.failed():
            self.handler.write("<<BLUE>>Test failed! Errors:")

            # Print out all the errors/warnings:
            for error in self.errors:
                self._print_message("<<RED>>Error:<<NORMAL>>\t",
                                    error, verbose)
            for warning in self.warnings:
                self._print_message("<<YELLOW>>Warning:<<NORMAL>> ",
                                    warning, verbose)
        else:
            self.handler.write("<<GREEN>>All tests succeeded!")

        if self.notices:
            for notice in self.notices:
                self._print_message(prefix="<<WHITE>>Notice:<<NORMAL>>\t",
                                    message=notice,
                                    verbose=verbose)

        if "is_jetpack" in self.metadata and verbose:
            self.handler.write("\n")
            self.handler.write("<<GREEN>>Jetpack add-on detected.<<NORMAL>>\n"
                               "Identified files:")
            if "jetpack_identified_files" in self.metadata:
                for filename, data in \
                        self.metadata["jetpack_identified_files"].items():
                    self.handler.write((" %s\n" % filename) +
                                       ("  %s : %s" % data))

            if "jetpack_unknown_files" in self.metadata:
                self.handler.write("Unknown files:")
                for filename in self.metadata["jetpack_unknown_files"]:
                    self.handler.write(" %s" % filename)


        self.handler.write("\n")
        if self.unfinished:
            self.handler.write("<<RED>>Validation terminated early")
            self.handler.write("Errors during validation are preventing"
                               "the validation proecss from completing.")
            self.handler.write("Use the <<YELLOW>>--determined<<NORMAL>> "
                               "flag to ignore these errors.")
            self.handler.write("\n")

        return buffer.getvalue()

    def _flatten_list(self, data):
        "Flattens nested lists into strings."

        if data is None:
            return ""
        if isinstance(data, types.StringTypes):
            return data
        elif isinstance(data, (list, tuple)):
            return "\n".join(self._flatten_list(x) for x in data)

    def _print_message(self, prefix, message, verbose=True):
        "Prints a message and takes care of all sorts of nasty code"

        # Load up the standard output.
        output = ["\n", prefix, message["message"]]

        # We have some extra stuff for verbose mode.
        if verbose:
            verbose_output = []

            # Detailed problem description.
            if message["description"]:
                verbose_output.append(
                    self._flatten_list(message["description"]))

            # Show the user what tier we're on
            verbose_output.append("\tTier:\t%d" % message["tier"])

            # If file information is available, output that as well.
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
            if message["column"] and message["column"] != 0:
                verbose_output.append("\tColumn:\t%d" % message["column"])

            if "context" in message and message["context"]:
                verbose_output.append("\tContext:")
                verbose_output.extend([("\t> %s" % x
                                        if x is not None
                                        else "\t>" + ("-" * 20))
                                       for x
                                       in message["context"]])

            # Stick it in with the standard items.
            output.append("\n")
            output.append("\n".join(verbose_output))

        # Send the final output to the handler to be rendered.
        self.handler.write(u''.join(map(unicodehelper.decode, output)))

    def supports_version(self, guid_set):
        """
        Returns whether a GUID set in for_appversions format is compatbile with
        the current supported applications list.
        """

        # Don't let the test run if we haven't parsed install.rdf yet.
        if self.supported_versions is None:
            raise Exception("Early compatibility test run before install.rdf "
                            "was parsed.")

        return self._compare_version(requirements=guid_set,
                                     support=self.supported_versions)

    def _compare_version(self, requirements, support):
        """
        Return whether there is an intersection between a support applications
        GUID set and a set of supported applications.
        """

        for guid in requirements:
            # If we support any of the GUIDs in the guid_set, test if any of
            # the provided versions for the GUID are supported.
            if (guid in support and
                any((detected_version in requirements[guid]) for
                    detected_version in support[guid])):
                return True

    def discard_unused_messages(self, ending_tier):
        """
        Delete messages from errors, warnings, and notices whose tier is
        greater than the ending tier.
        """

        stacks = [self.errors, self.warnings, self.notices]
        for stack in stacks:
            for message in stack:
                if message["tier"] > ending_tier:
                    stack.remove(message)
