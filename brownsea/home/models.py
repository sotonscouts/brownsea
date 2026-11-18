from django.db import models
from wagtail.admin.panels import FieldPanel

from brownsea.core.blocks import HomePageBlock, HomePageSidebarBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.mixins import RecentNewsMixin


class HomePage(RecentNewsMixin, BasePage):
    template = "pages/home/home_page.html"
    parent_page_types = ["wagtailcore.Page"]

    always_show_breadcrumbs = False

    introduction = models.TextField()
    body = StreamField(HomePageBlock())
    sidebar = StreamField(
        HomePageSidebarBlock(),
        blank=True,
        default=[{"type": "recent_news", "value": None}],
        help_text="The narrow column beside the body. Leave empty for a full-width page.",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("sidebar"),
        *RecentNewsMixin.news_panels,
    ]
