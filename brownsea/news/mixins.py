from urllib.parse import urlencode

from django import forms
from django.db import models
from django.utils.datastructures import MultiValueDict
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

from brownsea.news.filters import ArticleFilterSet, published_articles
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

    def get_news_filter_params(self):
        """The chosen facets as the news index's query string parameters, each with the slugs picked."""
        return {
            "type": [facet.slug for facet in self.news_types.all()],
            "audience": [facet.slug for facet in self.news_audiences.all()],
            "topic": [facet.slug for facet in self.news_topics.all()],
        }

    def get_recent_news(self):
        news_index_page = self.get_news_index_page()
        if news_index_page is None:
            return []

        articles = published_articles(under=news_index_page)
        excluded_types = list(self.news_exclude_types.all())
        if excluded_types:
            articles = articles.exclude(news_type__in=excluded_types)

        return ArticleFilterSet(MultiValueDict(self.get_news_filter_params()), queryset=articles).qs[:RECENT_NEWS_COUNT]

    def get_news_index_url(self):
        """The news index, narrowed to the same types, audiences and topics. Left-out types cannot be passed on."""
        news_index_page = self.get_news_index_page()
        if news_index_page is None:
            return None

        params = [(param, slug) for param, slugs in self.get_news_filter_params().items() for slug in slugs]
        url = news_index_page.url
        return f"{url}?{urlencode(params)}" if params else url

    def get_recent_news_context(self):
        return {"recent_news": self.get_recent_news(), "news_index_url": self.get_news_index_url()}
