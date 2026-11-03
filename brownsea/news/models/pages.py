import datetime

from django import forms
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.search import index

from brownsea.core.blocks import StoryBlock
from brownsea.core.models import Audience, BasePage, InPageNavMixin
from brownsea.core.utils import StreamField
from brownsea.news.models.snippets import NewsTopic, NewsType


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
    audiences = ParentalManyToManyField(
        "core.Audience",
        blank=True,
        related_name="+",
        help_text="Who this is for. Pages can show only the news for particular audiences.",
    )
    topics = ParentalManyToManyField(
        "news.NewsTopic",
        blank=True,
        related_name="articles",
        help_text="What this is about. Pages can show only the news on particular topics.",
    )
    introduction = models.TextField(
        help_text="The introduction for this article. Will be shown in article listings.",
    )
    body = StreamField(StoryBlock())

    content_panels = BasePage.content_panels + [
        FieldPanel("author"),
        MultiFieldPanel(
            [
                FieldPanel("news_type"),
                FieldPanel("audiences", widget=forms.CheckboxSelectMultiple),
                FieldPanel("topics", widget=forms.CheckboxSelectMultiple),
            ],
            "Classification",
        ),
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
    parent_page_types = ["home.HomePage"]
    subpage_types = ["news.ArticlePage"]

    max_count = 1

    introduction = models.TextField()

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        HelpPanel("All child articles will be listed."),
    ]
    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    def get_context(self, request):
        from brownsea.news.filters import filter_articles, published_articles

        context = super().get_context(request)

        facets = [
            NewsFacetFilter("type", "Type", NewsType.objects.all(), request.GET.getlist("type")),
            NewsFacetFilter("audience", "Audience", Audience.objects.all(), request.GET.getlist("audience")),
            NewsFacetFilter("topic", "Topic", NewsTopic.objects.all(), request.GET.getlist("topic")),
        ]
        type_filter, audience_filter, topic_filter = facets

        child_pages = filter_articles(
            published_articles(under=self),
            types=type_filter.selected_objects,
            audiences=audience_filter.selected_objects,
            topics=topic_filter.selected_objects,
        )

        page_number = request.GET.get("page")
        paginator = Paginator(
            child_pages,
            per_page=settings.APP_SEARCH_RESULTS_PER_PAGE,
        )

        context["sub_pages"] = paginator.get_page(page_number)
        context["facet_filters"] = [facet for facet in facets if facet.options]
        context["active_filter_count"] = sum(len(facet.selected) for facet in facets)
        context["is_filtered"] = bool(context["active_filter_count"])
        return context


class NewsFacetFilter:
    """One facet's choices on the news index, with the ones picked in the query string marked."""

    def __init__(self, param, label, choices, selected_slugs):
        self.param = param
        self.label = label
        self.options = list(choices)
        self.selected = {slug for slug in selected_slugs if slug in {option.slug for option in self.options}}

    @property
    def selected_objects(self):
        return [option for option in self.options if option.slug in self.selected]

    @property
    def choices(self):
        return [(option.slug, option.name, option.slug in self.selected) for option in self.options]
