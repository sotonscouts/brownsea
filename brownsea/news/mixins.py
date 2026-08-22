from django.db import models
from django.db.models.functions import Coalesce

from brownsea.news.models.pages import ArticlePage, NewsIndexPage


class RecentNewsMixin(models.Model):
    news_index_page = models.ForeignKey(
        "news.NewsIndexPage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["recent_news"] = self.get_recent_news()
        context["news_index_page"] = self.get_news_index_page()
        return context

    def get_news_index_page(self):
        if self.news_index_page:
            return self.news_index_page
        return self.get_children().type(NewsIndexPage).live().first()

    def get_recent_news(self):
        news_index_page = self.get_news_index_page()
        if news_index_page is None:
            return []

        child_pages = (
            ArticlePage.objects.live()
            .filter(show_in_menus=True)
            .descendant_of(news_index_page)
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
