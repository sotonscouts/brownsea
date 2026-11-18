from django.db import models
from django.db.models.functions import Coalesce

from brownsea.core.filters import AudienceFilter, FacetFilterSet, TaxonomyFilter
from brownsea.news.models.pages import ArticlePage
from brownsea.news.models.snippets import NewsTopic, NewsType


def published_articles(under=None):
    """Live articles shown in listings, newest first. Pass a page to limit them to its descendants."""
    articles = ArticlePage.objects.live().filter(show_in_menus=True)
    if under is not None:
        articles = articles.descendant_of(under)
    return (
        articles.annotate(
            date=Coalesce("publication_date", "first_published_at", output_field=models.DateField()),
        )
        .select_related("author_role__person", "news_type", "image")
        .order_by("-date", "-first_published_at")
    )


class ArticleFilterSet(FacetFilterSet):
    type = TaxonomyFilter(NewsType.objects.all(), field_name="news_type", label="Type")
    audience = AudienceFilter()
    topic = TaxonomyFilter(NewsTopic.objects.all(), field_name="topics", label="Topic")
