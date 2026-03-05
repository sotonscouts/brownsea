from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import ExternalEventCalendar


@register_snippet
class ExternalEventCalendarViewSet(SnippetViewSet):
    model = ExternalEventCalendar
    menu_label = "External Event Calendars"
    list_display = ("name", "slug")
    search_fields = ("name",)
