import types


LITERAL_TYPE = types.StringTypes + (int, float, long, bool, )


class Spec(object):
    """
    This object, when overridden with an object that implements a file format
    specification, will perform validation on a given parsed version of the
    format input.

    SPEC Node Documentation:
    ========================

    expected_type:
        A type object whose type the object should match.
    required_nodes:
        A list of nodes that are required for the current node.
    required_nodes_when:
        A dict of node name/lambda pairs. If the lambda evaluates to True, a
        node whose name corresponds to the node name is required.
        The current node is passed as a parameter to the lambda as the only
        argument.
    disallowed_nodes:
        A list of nodes that explicitly are disallowed in the current node.
    allowed_once_nodes:
        A list of nodes that are allowed only once.
    allowed_nodes:
        A list of nodes that are allowed multiple times.
    child_nodes:
        A dict of node definitions for nodes that can exist within this node.
    max_length:
        For sequence values only. An integer describing the maximum length of
        the string.
    not_empty:
        A boolean value describing whether the string/list/dict can be empty.
    values:
        A list of possible values for the node. Only applies to lists and
        literal nodes. For lists, each element of the list must belong to the
        list of possible values.
    process:
        A lambda function that returns a function to process the node. The
        lambda accepts one parameter (self) and should return a function that
        accepts two parameters (self, node).
    child_process:
        A lambda function (similar to `process` that returns a function to
        process a child node. The lambda accepts one parameter (self) and
        should return a function that accepts three parameters (self, node_name,
        node).
        If this is set, no further testing will take place on child nodes.
    """

    SPEC_NAME = "Specification"
    MORE_INFO = "You can find more info online."

    SPEC = None

    def __init__(self, data, err):
        self.data = self.parse(data)
        self.err = err

    def validate(self):
        # Validate the root node.
        root_name, root_node = self.get_root_node(self.data)
        root_val_result = self.validate_root_node(root_node)
        if root_val_result == False:
            return

        # Iterate the tree and validate as we go.
        self.iterate(root_name, root_node, self.SPEC)

    def parse(self, data): pass
    def validate_root_node(self, node): pass
    def get_root_node(self, data):
        """
        We expect this function to return a tuple:
        ("Root Node Name", root_node)
        """
        pass

    def has_attribute(self, node, key): pass
    def get_attribute(self, node, key): pass
    def has_child(self, node, child_name): pass
    def get_children(self, node):
        """
        This function should return a list of (child_name, child)-form tuples.
        """

    def iterate(self, branch_name, branch, spec_branch):
        """Iterate the tree of nodes and validate as we go."""

        # Check that the node is of the proper type. If it isn't, then we need
        # to stop iterating at this point.
        if not isinstance(branch, spec_branch["expected_type"]):
            self.err.error(
                err_id=("spec", "iterate", "bad_type"),
                error="%s's `%s` was of an unexpected type." %
                        (self.SPEC_NAME, branch_name),
                description=["While validating a %s, a `%s` was encountered "
                             "which is of an improper type." %
                                 (self.SPEC_NAME, branch_name),
                             "Found: %s" % repr(branch),
                             self.MORE_INFO])
            return

        # Handle any generic processing.
        if "process" in spec_branch:
            # Let the spec processor resolve the processor and then run the
            # processor.
            spec_branch["process"](self)(branch)

        if "not_empty" in spec_branch and not branch:
            self.err.error(
                err_id=("spec", "iterate", "empty"),
                error="`%s` is empty.",
                description=["A value was expected for `%s`, but one wasn't "
                             "found." % branch_name,
                             self.MORE_INFO])

        # If the node isn't an object...
        if not isinstance(branch, dict):
            if "values" in spec_branch and branch not in spec_branch["values"]:
                self.err.error(
                    err_id=("spec", "iterate", "bad_value"),
                    error="`%s` contains invalid value in %s" %
                            (branch_name, self.SPEC_NAME),
                    description=["A `%s` was encountered while validating a "
                                 "%s containing the value '%s'. This value is "
                                 "not appropriate for this type of element." %
                                     (branch_name, self.SPEC_NAME, branch),
                                 self.MORE_INFO])

            if ("max_length" in spec_branch and
                len(branch) > spec_branch["max_length"]):
                self.err.error(
                    err_id=("spec", "iterate", "max_length"),
                    error="`%s` has exceeded its maximum length.",
                    description=["`%s` has a maximum length (%d), which has "
                                 "been exceeded (%d)." %
                                     (branch_name, spec_branch["max_length"],
                                      len(branch)),
                                 self.MORE_INFO])

            # We've got nothing else to do with non-object nodes.
            return

        # If we need to process the child nodes individually, do that now.
        if "child_process" in spec_branch:
            processor = spec_branch["child_process"](self)
            for child_name, child in self.get_children(branch):
                processor(child_name, child)

            # If there's nothing else to do, don't go down that path.
            if ("required_nodes" not in spec_branch and
                "required_nodes_when" not in spec_branch and
                "disallowed_nodes" not in spec_branch):
                return

        considered_nodes = set()

        # Check that all required node as present.
        if "required_nodes" in spec_branch:
            considered_nodes.update(spec_branch["required_nodes"])

            for req_node in [n for n in spec_branch["required_nodes"] if
                             not self.has_child(branch, n)]:
                self.err.error(
                    err_id=("spec", "iterate", "missing_req"),
                    error="%s expecting `%s`" % (self.SPEC_NAME, req_node),
                    description=["The '%s' node of the %s expects a `%s` "
                                 "element, which was not found." %
                                     (branch_name, self.SPEC_NAME, req_node),
                                 self.MORE_INFO])

        # Check that conditionally required nodes are present.
        if "required_nodes_when" in spec_branch:
            considered_nodes.update(spec_branch["required_nodes_when"].keys())

            for req_node in [name for name, cond in
                             spec_branch["required_nodes_when"].items() if
                             cond(branch) and not self.has_child(branch, name)]:
                self.err.error(
                    err_id=("spec", "iterate", "missing_req_cond"),
                    error="%s expecting `%s`" % (self.SPEC_NAME, req_node),
                    description=["The '%s' node, under the current "
                                 "circumstances, is missing a `%s` element. "
                                 "This is a required condition of a %s." %
                                     (branch_name, req_node, self.SPEC_NAME),
                                 self.MORE_INFO])

        # Check that there are no disallowed nodes.
        if "disallowed_nodes" in spec_branch:
            disallowed_nodes = spec_branch["disallowed_nodes"]
            considered_nodes.update(disallowed_nodes)

            for dnode in [n for n in disallowed_nodes if
                          self.has_child(branch, n)]:
                self.err.error(
                    err_id=("spec", "iterate", "disallowed"),
                    error="%s found `%s`, which is not allowed." %
                            (self.SPEC_NAME, dnode),
                    description=["The '%s' node contains `%s`, which is a "
                                 "disallowed element. It should be removed." %
                                     (branch_name, dnode),
                                 self.MORE_INFO])

        if ("allowed_nodes" not in spec_branch and
            "allowed_once_nodes" not in spec_branch):
            return

        # Check that allowed nodes are obeyed.
        allowed_nodes = set(spec_branch.setdefault("allowed_nodes", []))
        allowed_once_nodes = spec_branch.setdefault("allowed_once_nodes", [])
        allowed_nodes.update(allowed_once_nodes)

        child_node_specs = spec_branch.setdefault("child_nodes", {})
        seen_nodes = set()
        warned_nodes = set()
        for child_name, child in self.get_children(branch):

            cspec_branch = None

            # Process the node first.
            if child_name in child_node_specs:
                cspec_branch = child_node_specs[child_name]
            elif "*" in child_node_specs:
                cspec_branch = child_node_specs["*"]

            if cspec_branch is not None:
                # If it's a lazily evaluated branch, evaluate it now.
                if isinstance(cspec_branch, types.LambdaType):
                    cspec_branch = cspec_branch(self)
                # Iterate the node.
                self.iterate(child_name, child, cspec_branch)

            # If we've seen a node before that's only supposed to be seen a
            # single time, warn about it.
            if child_name in allowed_once_nodes and child_name in seen_nodes:
                # Don't warn about the same node multiple times.
                if child_name in warned_nodes:
                    continue
                self.err.error(
                    err_id=("spec", "iterate", "allow_once_multiple"),
                    error="%s found `%s` more than once.",
                    description=["%ss may only contain a single `%s` element, "
                                 "however, it was encountered multiple times." %
                                     (self.SPEC_NAME, child_name),
                                 self.MORE_INFO])
                continue

            # Remember that we've seen this node.
            seen_nodes.add(child_name)
            if child_name in considered_nodes:
                continue

            # If the child isn't allowed, throw an error.
            if child_name not in allowed_nodes and "*" not in allowed_nodes:
                self.err.error(
                    err_id=("spec", "iterate", "not_allowed"),
                    error="`%s` is not a recognized element within a %s" %
                            (child_name, self.SPEC_NAME),
                    description=["While iterating a %s, a `%s` was found "
                                 "within a %s, which is not valid." %
                                     (self.SPEC_NAME, child_name, branch_name),
                                 self.MORE_INFO])

