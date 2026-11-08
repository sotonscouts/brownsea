import factory
from django.contrib.auth.models import Group, User
from factory.django import DjangoModelFactory
from wagtail.models import PageViewRestriction
from wagtail_factories import PageFactory, StreamFieldFactory, StructBlockFactory
from wagtail_factories.blocks import BlockFactory

from brownsea.core.blocks import HeadingBlock, QuoteBlock, RichTextBlock
from brownsea.home.models import HomePage
from brownsea.standard_pages.models import IndexPage, InfoPage


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


class AdminUserFactory(UserFactory):
    """A superuser, who can use the Wagtail admin and edit every page."""

    is_staff = True
    is_superuser = True


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Group {n}")


class PageViewRestrictionFactory(DjangoModelFactory):
    """Wagtail's own page privacy (password, group or logged-in restrictions)."""

    class Meta:
        model = PageViewRestriction

    restriction_type = PageViewRestriction.PASSWORD
    password = "secret"  # noqa: S105

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create and extracted:
            self.groups.set(extracted)


class HeadingBlockFactory(StructBlockFactory):
    class Meta:
        model = HeadingBlock

    heading = factory.Sequence(lambda n: f"Heading {n}")
    visually_hidden = False


class RichTextBlockFactory(BlockFactory):
    class Meta:
        model = RichTextBlock

    @classmethod
    def _construct_block(cls, block_class, *args, **kwargs):
        # `InfoPageFactory(body__0__text="Some <b>text</b>")` takes the rich text's HTML directly.
        return block_class().to_python(kwargs.get("value", "<p>Some text</p>"))


class QuoteBlockFactory(StructBlockFactory):
    class Meta:
        model = QuoteBlock

    quote = "Be prepared"
    author = ""


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
    # The admin defaults new pages to this (`BasePage.show_in_menus_default`), which index pages list children by.
    show_in_menus = True
    # e.g. `InfoPageFactory(body__0__heading__heading="First", body__1__text="<p>Some text</p>")`
    body = StreamFieldFactory(
        {
            "heading": factory.SubFactory(HeadingBlockFactory),
            "text": RichTextBlockFactory,
            "quote": factory.SubFactory(QuoteBlockFactory),
        }
    )


class IndexPageFactory(PageFactory):
    class Meta:
        model = IndexPage

    title = factory.Sequence(lambda n: f"Index page {n}")
    introduction = "Introduction"
    show_in_menus = True
