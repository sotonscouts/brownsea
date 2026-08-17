from django import template
from django.urls import reverse

from brownsea.core.magic_links import build_magic_link_url
from brownsea.core.models import PageAccessLevel

register = template.Library()


def _page_can_share_magic_links(request, page):
    if request is None or not request.user.is_authenticated:
        return False

    specific_page = page.specific
    if not hasattr(specific_page, "get_effective_access_level"):
        return False

    if specific_page.get_effective_access_level() != PageAccessLevel.MAGIC_LINK:
        return False

    return specific_page.permissions_for_user(request.user).can_edit()


@register.inclusion_tag("components/magic_links/share_button.html", takes_context=True)
def magic_link_share(context, page):
    request = context.get("request")
    if not _page_can_share_magic_links(request, page):
        return {"show": False}

    return {
        "show": True,
        "page": page,
        "panel_url": reverse("core:magic_links_panel", args=[page.id]),
    }


@register.simple_tag(takes_context=True)
def magic_link_share_url(context, link):
    return build_magic_link_url(link, context["request"])
