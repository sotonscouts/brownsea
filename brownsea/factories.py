import factory
from django.contrib.auth.models import Group, User
from factory.django import DjangoModelFactory
from wagtail_factories import PageFactory

from brownsea.home.models import HomePage
from brownsea.standard_pages.models import InfoPage


def publish(page):
    revision = page.save_revision()
    revision.publish()
    return page.specific


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "password")
    is_active = True


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Group {n}")


class HomePageFactory(PageFactory):
    class Meta:
        model = HomePage

    title = "Home"
    slug = factory.Sequence(lambda n: f"home-{n}")
    introduction = "Welcome"
    body = []


class InfoPageFactory(PageFactory):
    class Meta:
        model = InfoPage

    title = factory.Sequence(lambda n: f"Info page {n}")
    introduction = "Introduction"
    body = []
