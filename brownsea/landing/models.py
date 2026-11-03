from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import StreamValue
from wagtail.search import index

from brownsea.core.blocks import LandingPageBlock, LandingPageSidebarBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.mixins import RecentNewsMixin


def _linked_page_ids(stream):
    """Yield the id of every page linked from a stream, however deeply the links are nested."""
    for child in stream:
        if child.block_type == "page":
            if page := child.value.get("page"):
                yield page.id
        elif child.block_type == "quick_links":
            yield from _linked_page_ids(child.value["links"])
        elif isinstance(child.value, StreamValue):
            yield from _linked_page_ids(child.value)


class LandingPage(RecentNewsMixin, BasePage):
    template = "pages/landing/landing_page.html"
    parent_page_types = ["wagtailcore.Page", "home.HomePage", "standard_pages.IndexPage", "landing.LandingPage"]

    introduction = models.TextField()
    body = StreamField(LandingPageBlock())
    sidebar = StreamField(
        LandingPageSidebarBlock(),
        blank=True,
        help_text="An optional narrow column beside the body. Leave empty for a full-width page.",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("sidebar"),
        *RecentNewsMixin.news_panels,
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "Landing page"

    def get_linked_page_ids(self):
        """The pages linked from this page's body and sidebar, so automatic lists can leave them out."""
        return [*_linked_page_ids(self.body), *_linked_page_ids(self.sidebar)]
