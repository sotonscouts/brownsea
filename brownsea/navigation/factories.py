"""
Factories for the site navigation.

The navigation is a deeply nested StreamField, so it is built from raw stream data with the helpers below instead of
wagtail-factories' block factories, which cannot express the inline `ListBlock(StructBlock)` of secondary links.
"""

import uuid

from factory.django import DjangoModelFactory

from brownsea.navigation.models import NavigationSettings


def _list_item(value):
    # ListBlock only recognises its current storage format when items carry an id.
    return {"type": "item", "value": value, "id": str(uuid.uuid4())}


def link_value(title="", page=None, url=""):
    return {"page": page.pk if page else None, "external_url": url, "title": title}


def nav_link(title="", page=None, url="", groups=None, call_to_action=None):
    """
    A primary navigation item.

    `groups` maps a heading to the pages/URLs listed under it, e.g. `{"Policies": [safeguarding_page]}`. A group
    entry is either a page or a `(title, url)` tuple for external links.
    """
    secondary = []
    for heading, entries in (groups or {}).items():
        links = [
            _list_item(link_value(title=entry[0], url=entry[1]) if isinstance(entry, tuple) else link_value(page=entry))
            for entry in entries
        ]
        secondary.append(_list_item({"heading": heading, "links": links}))

    return {
        "type": "link",
        "value": {
            "link": link_value(title, page, url),
            "secondary_level_links": secondary,
            "call_to_action": call_to_action.pk if call_to_action else None,
        },
    }


class NavigationSettingsFactory(DjangoModelFactory):
    class Meta:
        model = NavigationSettings
        django_get_or_create = ("site",)

    primary_navigation = []
