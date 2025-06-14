from wagtail.admin.panels import FieldPanel

from brownsea.core.blocks import FeaturedSectionBlock
from brownsea.core.models import AbstractIndexPage
from brownsea.core.utils import StreamField


class HomePage(AbstractIndexPage):
    template = "pages/home/home_page.html"
    parent_page_types = ["wagtailcore.Page"]

    always_show_breadcrumbs = False

    featured_sections = StreamField(
        [
            ("featured_section", FeaturedSectionBlock()),
        ],
        max_num=1,
    )

    content_panels = AbstractIndexPage.content_panels + [
        FieldPanel("featured_sections"),
    ]
