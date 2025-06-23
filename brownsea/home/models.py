from django.db import models
from django.db.models.functions import Coalesce
from wagtail.admin.panels import FieldPanel

from brownsea.core.blocks import HomePageBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.models import ArticlePage
from brownsea.news.models.pages import NewsIndexPage


class HomePage(BasePage):
    template = "pages/home/home_page.html"
    parent_page_types = ["wagtailcore.Page"]

    always_show_breadcrumbs = False

    introduction = models.TextField()
    body = StreamField(HomePageBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["recent_news"] = self.get_recent_news()
        context["news_index_page"] = NewsIndexPage.objects.first()  # There is only one news index page
        return context

    def get_recent_news(self):
        child_pages = (
            ArticlePage.objects.live()
            .filter(show_in_menus=True)
            .annotate(
                date=Coalesce(
                    "publication_date",
                    "first_published_at",
                    output_field=models.DateField(),
                )
            )
            .select_related("news_type")
            .order_by("-date", "-first_published_at")
        )
        return child_pages[:3]
