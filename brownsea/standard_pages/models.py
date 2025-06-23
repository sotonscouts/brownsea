from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

from brownsea.core.blocks import StoryBlock
from brownsea.core.models import AbstractIndexPage, BasePage, InPageNavMixin
from brownsea.core.utils import StreamField


class IndexPage(AbstractIndexPage):
    template = "pages/standard_pages/index_page.html"

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        # FieldPanel('featured_pages'),
    ]


class InfoPage(InPageNavMixin, BasePage):
    template = "pages/standard_pages/info_page.html"

    introduction = models.TextField()
    body = StreamField(StoryBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]
