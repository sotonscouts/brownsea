from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

from brownsea.core.models import BasePage
from brownsea.core.utils import StreamField
from brownsea.people.blocks import PersonGroupBlock


class PersonListingPage(BasePage):
    template = "pages/people/people_listing_page.html"

    introduction = models.TextField()
    body = StreamField([("person_group", PersonGroupBlock())])

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.SearchField("body"),
    ]
