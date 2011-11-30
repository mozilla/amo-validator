from validator.compat import FX10_DEFINITION
from validator.constants import BUGZILLA_BUG


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(function):
        ENTITIES[name] = function
        return function
    return wrap


def entity(name, result=None):
    def return_wrap(t):
        output = ENTITIES[name](traverser=t)
        if result is not None:
            return result
        else:
            return output if output is not None else {}
    return {"value": return_wrap}


@register_entity("document.xmlEncoding")
def xmlEncoding(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlEncoding"),
        error="xmlEncoding removed in Gecko 10.",
        description='The "xmlEncoding" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("document.xmlVersion")
def xmlVersion(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlVersion"),
        error="xmlVersion removed in Gecko 10.",
        description='The "xmlVersion" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("document.xmlStandalone")
def xmlStandalone(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values", "xmlStandalone"),
        error="xmlStandalone removed in Gecko 10.",
        description='The "xmlStandalone" property has been removed. See %s for '
                    'more information.' % BUGZILLA_BUG % 687426,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)


@register_entity("nsIDOMNSHTMLFrameElement")
def nsIDOMNSHTMLFrameElement(traverser):
    traverser.err.error(
        err_id=("testcases_javascript_entity_values",
                "nsIDOMNSHTMLFrameElement"),
        error="nsIDOMNSHTMLFrameElement interface removed in Gecko 10.",
        description='The "nsIDOMNSHTMLFrameElement" interface has been '
                    'removed. You can use nsIDOMHTMLFrameElement instead. See '
                    '%s for more information.' % BUGZILLA_BUG % 677085,
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context,
        for_appversions=FX10_DEFINITION,
        compatibility_type="error",
        tier=5)

