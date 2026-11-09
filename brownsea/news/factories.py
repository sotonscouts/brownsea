import datetime

import factory
from factory.django import DjangoModelFactory
from wagtail_factories import PageFactory

from brownsea.news.models.pages import ArticlePage, NewsIndexPage
from brownsea.news.models.snippets import NewsTopic, NewsType


class NewsTypeFactory(DjangoModelFactory):
    class Meta:
        model = NewsType
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"News type {n}")
    slug = factory.Sequence(lambda n: f"news-type-{n}")


class NewsTopicFactory(DjangoModelFactory):
    class Meta:
        model = NewsTopic
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"News topic {n}")
    slug = factory.Sequence(lambda n: f"news-topic-{n}")


class NewsIndexPageFactory(PageFactory):
    class Meta:
        model = NewsIndexPage

    title = "News"
    slug = "news"
    introduction = "The latest news"


class ArticlePageFactory(PageFactory):
    """Pass `parent=` a news index. `audiences` and `topics` take lists, e.g. `ArticlePageFactory(topics=[topic])`."""

    class Meta:
        model = ArticlePage

    title = factory.Sequence(lambda n: f"Article {n}")
    introduction = "About this article"
    news_type = factory.SubFactory(NewsTypeFactory)
    publication_date = factory.LazyFunction(datetime.date.today)
    # The admin defaults new pages to this, and news listings only show pages that have it.
    show_in_menus = True
    body = []

    @factory.post_generation
    def audiences(self, create, extracted, **kwargs):
        if create and extracted:
            self.audiences.set(extracted)

    @factory.post_generation
    def topics(self, create, extracted, **kwargs):
        if create and extracted:
            self.topics.set(extracted)
