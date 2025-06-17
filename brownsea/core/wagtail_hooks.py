from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import CallToAction


class CallToActionSnippetViewSet(SnippetViewSet):
    model = CallToAction
    menu_label = "Calls to Action"
    list_display = ("title", "url")
    search_fields = ("title",)
    icon = "bullhorn"


register_snippet(CallToActionSnippetViewSet)


@hooks.register("register_icons")
def register_icons(icons):
    return icons + ["icons/bullhorn.svg"]
