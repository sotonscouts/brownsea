from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.search import index

from brownsea.core.blocks import LinkSectionBlock, TopicPageBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField


class TopicPage(BasePage):
    template = "pages/topics/topic_page.html"
    parent_page_types = ["wagtailcore.Page", "home.HomePage", "topics.TopicPage"]

    introduction = models.TextField()
    body = StreamField(TopicPageBlock())
    quick_links = StreamField(LinkSectionBlock(), blank=True, help_text="Quick links to display in the sidebar")

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        FieldPanel("quick_links"),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        # Handle search query
        search_query = request.GET.get("query", None)
        page_number = request.GET.get("page", 1)

        if search_query:
            search_results = self.search_within_topic(search_query)
            paginator = Paginator(search_results, settings.APP_SEARCH_RESULTS_PER_PAGE)
            try:
                search_results = paginator.page(page_number)
            except PageNotAnInteger:
                search_results = paginator.page(1)
            except EmptyPage:
                search_results = paginator.page(paginator.num_pages)

            context["search_query"] = search_query
            context["search_results"] = search_results
        else:
            context["search_query"] = None
            context["search_results"] = None

        return context

    def search_within_topic(self, query):
        """
        Search within this topic page and all its descendant pages.
        Returns a queryset of pages that match the search query.
        """
        # Get all descendant pages (this page and all its children, grandchildren, etc.)
        descendant_pages = Page.objects.descendant_of(self, inclusive=True).live()

        # Perform search on descendant pages
        search_results = descendant_pages.search(query)

        return search_results
