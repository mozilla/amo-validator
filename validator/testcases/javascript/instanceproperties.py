import re
import types

from validator.compat import FX10_DEFINITION
from validator.constants import BUGZILLA_BUG
import jstypes

def set_innerHTML(new_value, traverser):
    """Tests that values being assigned to innerHTML are not dangerous."""

    if not isinstance(new_value, jstypes.JSWrapper):
        new_value = jstypes.JSWrapper(new_value, traverser=traverser)

    if new_value.is_literal():
        literal_value = new_value.get_literal_value()
        if isinstance(literal_value, types.StringTypes):
            # Static string assignments

            # Test for on* attributes
            event_assignment = re.compile("<.+ on[a-z]+=")
            if event_assignment.search(literal_value.lower()):
                traverser.err.warning(
                    err_id=("testcases_javascript_instancetypes",
                            "set_innerHTML", "event_assignment"),
                    warning="Event handler assignment via innerHTML",
                    description=["When assigning event handlers, innerHTML "
                                 "should never be used. Rather, use a "
                                 "proper technique, like addEventListener.",
                                 "Event handler code: %s" %
                                    literal_value.encode("ascii", "replace")],
                    filename=traverser.filename,
                    line=traverser.line,
                    column=traverser.position,
                    context=traverser.context)
            else:
                # Everything checks out, but we still want to pass it through
                # the markup validator. Turn off strict mode so we don't get
                # warnings about malformed HTML.
                from validator.testcases.markup.markuptester import \
                                                                MarkupParser
                parser = MarkupParser(traverser.err, strict=False, debug=True)
                parser.process(traverser.filename, literal_value, "xul")

    else:
        # Variable assignments
        traverser.err.warning(
            err_id=("testcases_javascript_instancetypes", "set_innerHTML",
                        "variable_assignment"),
            warning="innerHTML should not be set dynamically",
            description="Due to both security and performance reasons, "
                        "innerHTML should not be set using dynamic "
                        "values. This can lead to security issues or "
                        "fairly serious performance degradation.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def set_on_event(new_value, traverser):
    "This ensures that on* properties are not assigned string values."
    if (new_value.is_literal() and
        isinstance(new_value.get_literal_value(), types.StringTypes)):
        traverser.err.warning(
            err_id=("testcases_javascript_instancetypes", "set_on_event",
                    "on*_str_assignment"),
            warning="on* property being assigned string",
            description="Event handlers in JavaScript should not be "
                        "assigned by setting an on* property to a "
                        "string of JS code. Rather, consider using "
                        "addEventListener.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def get_isElementContentWhitespace(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_instanceproperties", "get_iECW"),
        error="isElementContentWhitespace property removed in Gecko 10.",
        description='The "isElementContentWhitespace" property has been '
                    'removed. See %s for more information.' %
                        (BUGZILLA_BUG % 687422),
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


OBJECT_DEFINITIONS = {"innerHTML": {"set": set_innerHTML},
                      "isElementContentWhitespace":
                          {"get": get_isElementContentWhitespace}}


def get_operation(mode, property):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    if (property in OBJECT_DEFINITIONS and
        mode in OBJECT_DEFINITIONS[property]):

        return OBJECT_DEFINITIONS[property][mode]

    elif mode == "set" and unicode(property).startswith("on"):
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event

