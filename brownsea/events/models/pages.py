from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

from brownsea.core.blocks import StoryBlock
from brownsea.core.models import BasePage, InPageNavMixin
from brownsea.core.utils import StreamField

from .snippets import ExternalEventCalendar

__all__ = ["CalendarPage"]


class CalendarPage(InPageNavMixin, BasePage):
    template = "pages/events/calendar_page.html"

    introduction = models.TextField()
    body = StreamField(StoryBlock(), blank=True)
    external_calendar = models.ForeignKey(
        ExternalEventCalendar,
        on_delete=models.PROTECT,
        related_name="+",
        help_text="Select an external event calendar to display",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("external_calendar"),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]
