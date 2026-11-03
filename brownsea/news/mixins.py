from urllib.parse import urlencode

from django import forms
from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

from brownsea.news.filters import filter_articles, published_articles
from brownsea.news.models.pages import NewsIndexPage

RECENT_NEWS_COUNT = 3


class RecentNewsMixin(models.Model):
    """
    Lets a page show its latest news, narrowed by the news facets chosen on the page.

    Leaving a facet empty means "any". The page decides where the news appears.
    """

    news_types = ParentalManyToManyField(
        "news.NewsType",
        blank=True,
        related_name="+",
        verbose_name="Only these types",
        help_text="Leave empty to include every type.",
    )
    news_exclude_types = ParentalManyToManyField(
        "news.NewsType",
        blank=True,
        related_name="+",
        verbose_name="Leave out these types",
    )
    news_audiences = ParentalManyToManyField(
        "core.Audience",
        blank=True,
        related_name="+",
        verbose_name="Only these audiences",
        help_text="Leave empty to include every audience.",
    )
    news_topics = ParentalManyToManyField(
        "news.NewsTopic",
        blank=True,
        related_name="+",
        verbose_name="Only these topics",
        help_text="Leave empty to include every topic.",
    )

    news_panels = [
        MultiFieldPanel(
            [
                FieldPanel("news_types", widget=forms.CheckboxSelectMultiple),
                FieldPanel("news_exclude_types", widget=forms.CheckboxSelectMultiple),
                FieldPanel("news_audiences", widget=forms.CheckboxSelectMultiple),
                FieldPanel("news_topics", widget=forms.CheckboxSelectMultiple),
            ],
            "Recent news filters",
            help_text="Choose which news is listed. An article must match every group that has something ticked.",
            classname="collapsed",
        )
    ]

    class Meta:
        abstract = True

    def get_news_index_page(self):
        return NewsIndexPage.objects.live().first()

    def get_news_filters(self):
        return {
            "types": list(self.news_types.all()),
            "exclude_types": list(self.news_exclude_types.all()),
            "audiences": list(self.news_audiences.all()),
            "topics": list(self.news_topics.all()),
        }

    def get_recent_news(self):
        news_index_page = self.get_news_index_page()
        if news_index_page is None:
            return []

        return filter_articles(published_articles(under=news_index_page), **self.get_news_filters())[:RECENT_NEWS_COUNT]

    def get_news_index_url(self):
        """The news index, narrowed to the same types, audiences and topics. Left-out types cannot be passed on."""
        news_index_page = self.get_news_index_page()
        if news_index_page is None:
            return None

        filters = self.get_news_filters()
        params = [
            (param, facet.slug)
            for param, facets in (
                ("type", filters["types"]),
                ("audience", filters["audiences"]),
                ("topic", filters["topics"]),
            )
            for facet in facets
        ]
        url = news_index_page.url
        return f"{url}?{urlencode(params)}" if params else url

    def get_recent_news_context(self):
        return {"recent_news": self.get_recent_news(), "news_index_url": self.get_news_index_url()}
