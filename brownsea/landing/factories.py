import factory
from wagtail_factories import PageFactory

from brownsea.landing.models import LandingPage


class LandingPageFactory(PageFactory):
    class Meta:
        model = LandingPage

    title = factory.Sequence(lambda n: f"Landing page {n}")
    introduction = "Introduction"
    body = []
    sidebar = []
