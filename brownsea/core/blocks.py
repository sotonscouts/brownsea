from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

GROUP_TEXT = "1. Text and Headings"
GROUP_CALLOUTS = "2. Callouts"


class LinkItemValue(blocks.StructValue):
    @property
    def url(self):
        if self.get("page"):
            return self.get("page").url
        return self.get("url")

    @property
    def title(self):
        if self.get("page"):
            return self.get("page").title
        return self.get("title")

    @property
    def description(self):
        if self.get("page"):
            return self.get("page").specific.introduction
        return self.get("description")


class AccordionItemBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    content = blocks.RichTextBlock(required=True)


class AccordionBlock(blocks.StructBlock):
    sections = blocks.ListBlock(AccordionItemBlock())

    class Meta:
        template = "components/streamfield/blocks/accordion_block.html"
        icon = "collapse-down"
        label = "Accordion"
        group = GROUP_CALLOUTS


class ExternalLinkBlock(blocks.StructBlock):
    url = blocks.URLBlock()
    title = blocks.CharBlock()
    description = blocks.RichTextBlock()

    class Meta:
        template = "components/streamfield/blocks/link_card_block.html"
        icon = "link"
        label = "External Link"
        value_class = LinkItemValue


class FeaturedExternalLinkBlock(ExternalLinkBlock):
    image = ImageChooserBlock()

    class Meta:
        template = "components/streamfield/blocks/featured_item_block.html"
        icon = "link"
        label = "External Link"
        value_class = LinkItemValue


class PageLinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()

    class Meta:
        template = "components/streamfield/blocks/link_card_block.html"
        icon = "folder-open-inverse"
        label = "Page Link"
        value_class = LinkItemValue


class FeaturedPageBlock(PageLinkBlock):
    image = ImageChooserBlock()

    class Meta:
        template = "components/streamfield/blocks/featured_item_block.html"
        icon = "folder-open-inverse"
        label = "Featured Page"
        value_class = LinkItemValue


class FeaturedSectionBlock(blocks.StreamBlock):
    page = FeaturedPageBlock()
    external_link = FeaturedExternalLinkBlock()

    class Meta:
        template = "components/streamfield/blocks/featured_section_block.html"
        icon = "folder-open-inverse"
        label = "Featured Section"
        max_num = 2


class LinkSectionBlock(blocks.StreamBlock):
    page = PageLinkBlock()
    external_link = ExternalLinkBlock()

    class Meta:
        template = "components/streamfield/blocks/link_section_block.html"
        icon = "link"
        label = "Link Section"
        min_num = 1


class HeadingBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)

    class Meta:
        template = "components/streamfield/blocks/heading_block.html"
        icon = "title"
        label = "Heading"
        help_text = "A title or heading for a section of content."
        group = GROUP_TEXT


class RichTextBlock(blocks.RichTextBlock):
    class Meta:
        template = "components/streamfield/blocks/rich_text_block.html"
        icon = "pilcrow"
        label = "Rich Text"
        group = GROUP_TEXT


class QuoteBlock(blocks.StructBlock):
    quote = blocks.TextBlock(required=True)
    author = blocks.CharBlock(required=False)

    class Meta:
        template = "components/streamfield/blocks/quote_block.html"
        icon = "openquote"
        label = "Quote"
        help_text = "A quote from a source."
        group = GROUP_CALLOUTS


class WarningCalloutBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, help_text="A short, clearly worded heading.")
    content = blocks.RichTextBlock(
        required=True,
        help_text="Make the callout concise, specific and self-contained.",
    )

    class Meta:
        template = "components/streamfield/blocks/warning_callout_block.html"
        icon = "warning"
        label = "Warning Callout"
        help_text = "Use for time-critical information or content."
        group = GROUP_CALLOUTS


class StoryBlock(blocks.StreamBlock):
    accordion = AccordionBlock()
    heading = HeadingBlock()
    text = RichTextBlock()
    quote = QuoteBlock()
    warning_callout = WarningCalloutBlock()


class HomePageBlock(blocks.StreamBlock):
    featured_sections = FeaturedSectionBlock()
    link_sections = LinkSectionBlock()
