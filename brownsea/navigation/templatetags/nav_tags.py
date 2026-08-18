from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("components/navigation/primary_nav.html", takes_context=True)
def primary_nav(context):
    request = context["request"]
    theme_settings = context.get("theme_settings")
    return {
        "unit_name": theme_settings.unit_name if theme_settings else "",
        "logo": theme_settings.logo if theme_settings else None,
        "APP_SHOW_MENU_WHEN_UNAUTHENTICATED": settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED,
        "primary_nav": context["settings"]["navigation"]["NavigationSettings"].primary_navigation,
        "request": request,
    }
