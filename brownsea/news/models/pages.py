import datetime

from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models.functions import Coalesce
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.search import index

from brownsea.core.blocks import StoryBlock
from brownsea.core.models import BasePage, InPageNavMixin
from brownsea.core.utils import StreamField


class ArticlePage(InPageNavMixin, BasePage):
    template = "pages/news/article_page.html"
    parent_page_types = ["news.NewsIndexPage"]
    subpage_types = []
    max_count = None  # Unlimited articles

    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="The main image for this article. Will be shown at the top of the article and in article listings.",
    )
    publication_date = models.DateField(
        "Publication date",
        null=True,
        blank=True,
        help_text="The date the article was published. If not set, the current date will be used.",
    )
    author = models.ForeignKey(
        "core.Author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    news_type = models.ForeignKey(
        "news.NewsType",
        on_delete=models.PROTECT,
    )
    introduction = models.TextField(
        help_text="The introduction for this article. Will be shown in article listings.",
    )
    body = StreamField(StoryBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel("author"),
        FieldPanel("news_type"),
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("introduction"),
                FieldPanel("body"),
            ],
            "Content",
        ),
    ]
    promote_panels = [
        FieldPanel("publication_date"),
    ] + BasePage.promote_panels
    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    @property
    def display_date(self) -> datetime.date | None:
        if self.publication_date:
            return self.publication_date
        elif self.first_published_at:
            return self.first_published_at.date()
        return None


class NewsIndexPage(BasePage):
    template = "pages/news/news_index_page.html"
    subpage_types = ["news.ArticlePage"]
    max_count = 1  # Only one news index page

    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel("All child articles will be listed."),
    ]
    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    def get_context(self, request):
        context = super().get_context(request)

        child_pages = (
            ArticlePage.objects.live()
            .filter(show_in_menus=True)
            .descendant_of(self)
            .annotate(
                date=Coalesce(
                    "publication_date",
                    "first_published_at",
                    output_field=models.DateField(),
                )
            )
            .select_related("author", "news_type")
            .order_by("-date", "-first_published_at")
        )

        page_number = request.GET.get("page")
        paginator = Paginator(
            child_pages,
            per_page=settings.APP_SEARCH_RESULTS_PER_PAGE,
        )

        context["sub_pages"] = paginator.get_page(page_number)
        return context
