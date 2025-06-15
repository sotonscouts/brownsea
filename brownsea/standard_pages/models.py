from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

from brownsea.core.blocks import HeadingBlock, StoryBlock
from brownsea.core.models import AbstractIndexPage, BasePage
from brownsea.core.utils import StreamField


class IndexPage(AbstractIndexPage):
    template = "pages/standard_pages/index_page.html"

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        # FieldPanel('featured_pages'),
    ]


class InfoPage(BasePage):
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

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        headings = []
        for block in self.body:
            if isinstance(block.block, HeadingBlock):
                headings.append(block.value["heading"])

        # If there are 3 or more heading blocks, add them to the context, so
        # that the in-page navigation is shown
        if len(headings) >= 3:
            context["in_page_nav"] = headings
        else:
            context["in_page_nav"] = None

        return context
