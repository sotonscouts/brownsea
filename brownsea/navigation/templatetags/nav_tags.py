from django import template

register = template.Library()


@register.inclusion_tag("components/navigation/primary_nav.html", takes_context=True)
def primary_nav(context):
    request = context["request"]
    return {
        "primary_nav": context["settings"]["navigation"]["NavigationSettings"].primary_navigation,
        "request": request,
    }
