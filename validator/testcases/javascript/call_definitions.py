import copy
import types

import actions
import traverser as js_traverser
import predefinedentities
from jstypes import *

# Function prototypes should implement the following:
#  wrapper : The JSWrapper instace that is being called
#  arguments : A list of argument nodes; untraversed
#  traverser : The current traverser object

def xpcom_constructor(method, extend=False, mutate=False, pretraversed=False):
    """Returns a function which wraps an XPCOM class instantiation function."""

    def definition(wrapper, arguments, traverser):
        """Wraps an XPCOM class instantiation function."""

        if not arguments:
            return None

        traverser._debug("(XPCOM Encountered)")

        if not pretraversed:
            arguments = [traverser._traverse_node(x) for x in arguments]
        argz = arguments[0]

        if not argz.is_global or "xpcom_map" not in argz.value:
            argz = JSWrapper(traverser=traverser)
            argz.value = {"xpcom_map": lambda: {"value": {}}}

        traverser._debug("(Building XPCOM...)")

        inst = traverser._build_global(method,
                                       copy.deepcopy(argz.value["xpcom_map"]()))
        inst.value["overwriteable"] = True

        if extend or mutate:
            # FIXME: There should be a way to get this without
            # traversing the call chain twice.
            parent = actions.trace_member(traverser, wrapper["callee"]["object"])

            if mutate and not (parent.is_global and
                               isinstance(parent.value, dict) and
                               "value" in parent.value):
                # Assume that the parent object is a first class
                # wrapped native
                parent.value = inst.value

                # FIXME: Only objects marked as global are processed
                # as XPCOM instances
                parent.is_global = True

            if isinstance(parent.value, dict):
                if extend and mutate:
                    if callable(parent.value["value"]):
                        parent.value["value"] = \
                            copy.deepcopy(parent.value["value"](t=traverser))

                    parent.value["value"].update(inst.value["value"])
                    return parent

                if extend:
                    inst.value["value"].update(parent.value["value"])

                if mutate:
                    parent.value = inst.value

        return inst
    definition.__name__ = "xpcom_%s" % str(method)
    return definition

