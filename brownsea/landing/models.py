from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

from brownsea.core.blocks import LandingPageBlock, LandingPageSidebarBlock, linked_page_ids
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.mixins import RecentNewsMixin


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
        return [*linked_page_ids(self.body), *linked_page_ids(self.sidebar)]
