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

def xpcom_constructor(method):
    "Wraps the XPCOM class instantiation function."

    def definition(wrapper, arguments, traverser):
        "Wraps the XPCOM class instantiation function."

        if not arguments:
            return None

        traverser._debug("(XPCOM Encountered)")

        arguments = [traverser._traverse_node(x) for x in arguments]
        argz = arguments[0]

        if not argz.is_global or "xpcom_map" not in argz.value:
            return None

        traverser._debug("(Building XPCOM...)")

        inst = traverser._build_global(method,
                                       copy.deepcopy(argz.value["xpcom_map"]()))
        return inst
    definition.__name__ = "xpcom_%s" % str(method)
    return definition

