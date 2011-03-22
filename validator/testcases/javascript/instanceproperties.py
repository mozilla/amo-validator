import re
import types


def set_innerHTML(new_value, traverser):
    "Tests that values being assigned to innerHTML are not dangerous"

    literal_value = new_value.get_literal_value()
    if isinstance(literal_value, types.StringTypes):
        # Static string assignments

        # Test for on* attributes
        event_assignment = re.compile("<.+ on[a-z]+=")
        if event_assignment.search(literal_value.lower()):
            traverser.err.warning(("testcases_javascript_instancetypes",
                                   "set_innerHTML",
                                   "event_assignment"),
                                  "Event handler assignment via innerHTML",
                                  "When assigning event handlers, innerHTML "
                                  "should never be used. Rather, use a "
                                  "proper technique, like addEventListener.",
                                  filename=traverser.filename,
                                  line=traverser.line,
                                  column=traverser.position,
                                  context=traverser.context)
        else:
            # Everything checks out, but we still want to pass it through the
            # markup validator. Turn off strict mode so we don't get warnings
            # about malformed HTML.
            from validator.testcases.markup.markuptester import MarkupParser
            parser = MarkupParser(traverser.err, strict=False, debug=True)
            parser.process(traverser.filename, literal_value, "xul")

    else:
        # Variable assignments
        traverser.err.warning(("testcases_javascript_instancetypes",
                               "set_innerHTML",
                               "variable_assignment"),
                              "innerHTML should not be set dynamically",
                              "Due to both security and performance reasons, "
                              "innerHTML should not be set using dynamic "
                              "values. This can lead to security issues or "
                              "fairly serious performance degredation.",
                              filename=traverser.filename,
                              line=traverser.line,
                              column=traverser.position,
                              context=traverser.context)


def set_on_event(new_value, traverser):
    "This ensures that on* properties are not assigned string values."

    if (new_value.is_literal() and
        isinstance(new_value.get_literal_value(), types.StringTypes)):
        traverser.err.warning(("testcases_javascript_instancetypes",
                               "set_on_event",
                               "on*_str_assignment"),
                              "on* property being assigned string",
                              "Event handlers in JavaScript should not be "
                              "assigned by setting an on* property to a "
                              "string of JS code. Rather, consider using "
                              "addEventListerner.",
                              filename=traverser.filename,
                              line=traverser.line,
                              column=traverser.position,
                              context=traverser.context)


OBJECT_DEFINITIONS = {"innerHTML": {"set": set_innerHTML}}


def get_operation(mode, property):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    if (property in OBJECT_DEFINITIONS and
        mode in OBJECT_DEFINITIONS[property]):

        return OBJECT_DEFINITIONS[property][mode]

    elif mode == "set" and  property.startswith("on"):
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event

