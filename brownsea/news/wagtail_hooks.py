from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import NewsType


@register_snippet
class NewsTypeViewSet(SnippetViewSet):
    model = NewsType
    menu_label = "News Types"
    list_display = ("name", "slug")
    search_fields = ("name",)
