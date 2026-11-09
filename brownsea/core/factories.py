import factory
from factory.django import DjangoModelFactory
from wagtail.rich_text import RichText
from wagtail_factories import ImageChooserBlockFactory, PageChooserBlockFactory, StreamBlockFactory, StructBlockFactory

from brownsea.core.blocks import (
    ExternalLinkBlock,
    FeaturedExternalLinkBlock,
    FeaturedPageBlock,
    FeaturedSectionBlock,
    LinkSectionBlock,
    PageLinkBlock,
)
from brownsea.core.models import AlertBannerSettings, Audience, Author, CallToAction, PageMagicLink, ThemeSettings


class AudienceFactory(DjangoModelFactory):
    class Meta:
        model = Audience
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Audience {n}")
    slug = factory.Sequence(lambda n: f"audience-{n}")


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Sequence(lambda n: f"Author {n}")
    role = "Volunteer"


class CallToActionFactory(DjangoModelFactory):
    class Meta:
        model = CallToAction

    title = factory.Sequence(lambda n: f"Call to action {n}")
    summary = "Find out more"
    link_text = "Find out more"
    external_url = "https://example.com/"


# Site settings are created lazily by Wagtail (`for_site`), so reuse the row if one already exists.
class ThemeSettingsFactory(DjangoModelFactory):
    class Meta:
        model = ThemeSettings
        django_get_or_create = ("site",)

    colour = "white"
    unit_name = "Test Unit"


class AlertBannerSettingsFactory(DjangoModelFactory):
    class Meta:
        model = AlertBannerSettings
        django_get_or_create = ("site",)

    enabled = True
    message = "Something you should know"
    type = "info"


class PageMagicLinkFactory(DjangoModelFactory):
    class Meta:
        model = PageMagicLink

    label = factory.Sequence(lambda n: f"Magic link {n}")


class PageLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = PageLinkBlock

    page = factory.SubFactory(PageChooserBlockFactory)


class ExternalLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = ExternalLinkBlock

    url = "https://example.com/"
    title = factory.Sequence(lambda n: f"External link {n}")
    # Takes the rich text's HTML, e.g. `external_link__description="<p>Order badges</p>"`.
    description = factory.Transformer("<p>An external site</p>", transform=RichText)


class FeaturedPageBlockFactory(StructBlockFactory):
    class Meta:
        model = FeaturedPageBlock

    page = factory.SubFactory(PageChooserBlockFactory)
    image = factory.SubFactory(ImageChooserBlockFactory)


class FeaturedExternalLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = FeaturedExternalLinkBlock

    url = "https://example.com/"
    title = factory.Sequence(lambda n: f"Featured link {n}")
    # Takes the rich text's HTML, e.g. `external_link__description="<p>Order badges</p>"`.
    description = factory.Transformer("<p>An external site</p>", transform=RichText)
    image = factory.SubFactory(ImageChooserBlockFactory)


class FeaturedSectionBlockFactory(StreamBlockFactory):
    """e.g. `body__0__featured_sections__0__page__page=page`."""

    class Meta:
        model = FeaturedSectionBlock

    page = factory.SubFactory(FeaturedPageBlockFactory)
    external_link = factory.SubFactory(FeaturedExternalLinkBlockFactory)


class LinkSectionBlockFactory(StreamBlockFactory):
    class Meta:
        model = LinkSectionBlock

    page = factory.SubFactory(PageLinkBlockFactory)
    external_link = factory.SubFactory(ExternalLinkBlockFactory)
