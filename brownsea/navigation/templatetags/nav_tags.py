from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("components/navigation/primary_nav.html", takes_context=True)
def primary_nav(context):
    request = context["request"]
    return {
        "APP_LOGO_UNIT_NAME": settings.APP_LOGO_UNIT_NAME,
        "APP_SHOW_MENU_WHEN_UNAUTHENTICATED": settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED,
        "primary_nav": context["settings"]["navigation"]["NavigationSettings"].primary_navigation,
        "request": request,
    }
