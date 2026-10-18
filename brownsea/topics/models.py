from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page
from wagtail.search import index

from brownsea.core.blocks import LinkSectionBlock, TopicPageBlock
from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.news.mixins import RecentNewsMixin


class TopicPage(RecentNewsMixin, BasePage):
    template = "pages/topics/topic_page.html"
    parent_page_types = ["wagtailcore.Page", "home.HomePage", "topics.TopicPage", "standard_pages.IndexPage"]

    introduction = models.TextField()
    body = StreamField(TopicPageBlock())

    child_page_index_title = models.CharField(blank=True)
    display_child_page_index = models.BooleanField(
        default=False, help_text="Show a list of child pages at the bottom of the topic, similar to an index."
    )

    quick_links = StreamField(
        LinkSectionBlock(min_num=0),
        blank=True,
        help_text="Quick links to display in the sidebar",
        use_json_field=True,
    )
    news_content_type_plural = models.CharField(
        max_length=255,
        blank=False,
        help_text="The plural name of the news content type to display in the recent news section.",
        default="news",
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("child_page_index_title"),
                FieldPanel("display_child_page_index"),
            ],
            "Extra Links",
        ),
        FieldPanel("quick_links"),
        MultiFieldPanel(
            [
                FieldPanel("news_index_page"),
                FieldPanel("news_content_type_plural"),
            ],
            "Recent News Section",
        ),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]

    def get_featured_page_ids(self):
        """
        Recursively/nestedly extract page IDs from LinkSectionBlock,
        FeaturedSectionBlock, PageLinkBlock, and FeaturedPageBlock.
        """
        featured_ids = []

        for block in self.body:
            # 1. Direct PageLinkBlock or FeaturedPageBlock
            if block.block_type in ("page", "featured_page"):
                if block.value and block.value.get("page"):
                    featured_ids.append(block.value["page"].id)

            # 2. Nested inside LinkSectionBlock or FeaturedSectionBlock (StreamBlocks)
            elif block.block_type in ("link_sections", "featured_sections"):
                for child_block in block.value:
                    # Look for page or featured_page blocks inside the stream section
                    if child_block.block_type in ("page", "featured_page"):
                        page_obj = child_block.value.get("page")
                        if page_obj:
                            featured_ids.append(page_obj.id)

        return featured_ids

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

        if self.display_child_page_index:
            context["remaining_pages"] = (
                self.get_children().live().public().exclude(id__in=self.get_featured_page_ids()).specific()
            )
        else:
            context["remaining_pages"] = self.get_children().none()

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
