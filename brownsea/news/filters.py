from django.db import models
from django.db.models.functions import Coalesce

from brownsea.news.models.pages import ArticlePage


def published_articles(under=None):
    """Live articles shown in listings, newest first. Pass a page to limit them to its descendants."""
    articles = ArticlePage.objects.live().filter(show_in_menus=True)
    if under is not None:
        articles = articles.descendant_of(under)
    return (
        articles.annotate(
            date=Coalesce("publication_date", "first_published_at", output_field=models.DateField()),
        )
        .select_related("author", "news_type", "image")
        .order_by("-date", "-first_published_at")
    )


def filter_articles(articles, *, types=(), exclude_types=(), audiences=(), topics=()):
    """
    Narrow articles by the news facets. Each argument is a list of facet objects (or their ids).

    An empty list means "any". Within one facet an article matches if it has any of the chosen values, and an
    article must match every facet that has values.
    """
    if types:
        articles = articles.filter(news_type__in=types)
    if exclude_types:
        articles = articles.exclude(news_type__in=exclude_types)
    if audiences:
        articles = articles.filter(pk__in=ArticlePage.objects.filter(audiences__in=audiences).values("pk"))
    if topics:
        articles = articles.filter(pk__in=ArticlePage.objects.filter(topics__in=topics).values("pk"))
    return articles
