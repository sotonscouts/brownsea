import factory
from wagtail_factories import (
    ImageChooserBlockFactory,
    PageChooserBlockFactory,
    PageFactory,
    StreamBlockFactory,
    StreamFieldFactory,
    StructBlockFactory,
)
from wagtail_factories.blocks import BlockFactory

from brownsea.core.blocks import (
    ChildPagesBlock,
    LogoExternalLinkBlock,
    LogoGridBlock,
    LogoPageLinkBlock,
    QuickExternalLinkBlock,
    QuickLinksBlock,
    QuickLinksStreamBlock,
    TaskTileExternalBlock,
    TaskTilePageBlock,
    TaskTilesBlock,
)
from brownsea.core.factories import (
    FeaturedSectionBlockFactory,
    LinkSectionBlockFactory,
    PageLinkBlockFactory,
)
from brownsea.factories import HeadingBlockFactory, RichTextBlockFactory
from brownsea.landing.models import LandingPage


class LogoPageLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = LogoPageLinkBlock

    page = factory.SubFactory(PageChooserBlockFactory)
    image = factory.SubFactory(ImageChooserBlockFactory)


class LogoExternalLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = LogoExternalLinkBlock

    url = "https://example.com/"
    title = factory.Sequence(lambda n: f"Logo {n}")
    image = factory.SubFactory(ImageChooserBlockFactory)


class LogoGridBlockFactory(StreamBlockFactory):
    class Meta:
        model = LogoGridBlock

    page = factory.SubFactory(LogoPageLinkBlockFactory)
    external_link = factory.SubFactory(LogoExternalLinkBlockFactory)


class TaskTilePageBlockFactory(StructBlockFactory):
    class Meta:
        model = TaskTilePageBlock

    icon = "help"
    label = factory.Sequence(lambda n: f"Task {n}")
    page = factory.SubFactory(PageChooserBlockFactory)


class TaskTileExternalBlockFactory(StructBlockFactory):
    class Meta:
        model = TaskTileExternalBlock

    icon = "help"
    label = factory.Sequence(lambda n: f"Task {n}")
    url = "https://example.com/"


class TaskTilesBlockFactory(StreamBlockFactory):
    class Meta:
        model = TaskTilesBlock

    page = factory.SubFactory(TaskTilePageBlockFactory)
    external_link = factory.SubFactory(TaskTileExternalBlockFactory)


class ChildPagesBlockFactory(StructBlockFactory):
    class Meta:
        model = ChildPagesBlock

    title = ""
    layout = "cards"
    show_introductions = True


class QuickExternalLinkBlockFactory(StructBlockFactory):
    class Meta:
        model = QuickExternalLinkBlock

    url = "https://example.com/"
    title = factory.Sequence(lambda n: f"Quick link {n}")


class QuickLinksStreamBlockFactory(StreamBlockFactory):
    class Meta:
        model = QuickLinksStreamBlock

    page = factory.SubFactory(PageLinkBlockFactory)
    external_link = factory.SubFactory(QuickExternalLinkBlockFactory)


class QuickLinksBlockFactory(StructBlockFactory):
    class Meta:
        model = QuickLinksBlock

    heading = "Quick links"
    links = factory.SubFactory(QuickLinksStreamBlockFactory)


class StaticBlockFactory(BlockFactory):
    """A block with no settings, such as recent news: `LandingPageFactory(sidebar__0__recent_news=True)`."""

    @classmethod
    def _construct_block(cls, block_class, *args, **kwargs):
        return block_class().to_python(None)

    class Meta:
        model = object


class LandingPageFactory(PageFactory):
    """
    e.g. `LandingPageFactory(body__0__link_sections__0__page__page=page,
    sidebar__0__quick_links__links__0__page__page=page)`.
    """

    class Meta:
        model = LandingPage

    title = factory.Sequence(lambda n: f"Landing page {n}")
    introduction = "Introduction"
    body = StreamFieldFactory(
        {
            "heading": factory.SubFactory(HeadingBlockFactory),
            "text": RichTextBlockFactory,
            "featured_sections": factory.SubFactory(FeaturedSectionBlockFactory),
            "link_sections": factory.SubFactory(LinkSectionBlockFactory),
            "logo_grid": factory.SubFactory(LogoGridBlockFactory),
            "task_tiles": factory.SubFactory(TaskTilesBlockFactory),
            "child_pages": factory.SubFactory(ChildPagesBlockFactory),
        }
    )
    sidebar = StreamFieldFactory(
        {
            "quick_links": factory.SubFactory(QuickLinksBlockFactory),
            "recent_news": StaticBlockFactory,
        }
    )
