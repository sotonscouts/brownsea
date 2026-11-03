from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Author, CallToAction
from .views.page_types import page_types_guide


@register_snippet
class AuthorSnippetViewSet(SnippetViewSet):
    model = Author
    menu_label = "Authors"
    list_display = ("name", "role")
    search_fields = ("name",)
    icon = "user"


@register_snippet
class CallToActionSnippetViewSet(SnippetViewSet):
    model = CallToAction
    menu_label = "Calls to Action"
    list_display = ("title", "url")
    search_fields = ("title",)
    icon = "bullhorn"


@hooks.register("register_icons")
def register_icons(icons):
    return icons + ["icons/bullhorn.svg"]


@hooks.register("register_admin_urls")
def register_page_types_url():
    return [path("page-types/", page_types_guide, name="page_types_guide")]


@hooks.register("register_help_menu_item")
def register_page_types_menu_item():
    return MenuItem("Page types", reverse("page_types_guide"), icon_name="doc-full", order=1050)
