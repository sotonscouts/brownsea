from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Author, CallToAction


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
