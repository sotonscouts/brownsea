from django.db import models
from wagtail.admin.panels import FieldPanel

from brownsea.core.blocks import HomePageBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.mixins import RecentNewsMixin


class HomePage(RecentNewsMixin, BasePage):
    template = "pages/home/home_page.html"
    parent_page_types = ["wagtailcore.Page"]

    always_show_breadcrumbs = False

    introduction = models.TextField()
    body = StreamField(HomePageBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("news_index_page"),
    ]
