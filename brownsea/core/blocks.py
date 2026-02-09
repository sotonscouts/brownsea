from wagtail import blocks
from wagtail.contrib.table_block.blocks import TableBlock as BaseTableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock

GROUP_TEXT = "1. Text and Headings"
GROUP_CALLOUTS = "2. Callouts"
GROUP_MEDIA = "3. Media & Embeds"


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
        group = GROUP_CALLOUTS
        max_num = 2


class LinkSectionBlock(blocks.StreamBlock):
    page = PageLinkBlock()
    external_link = ExternalLinkBlock()

    class Meta:
        template = "components/streamfield/blocks/link_section_block.html"
        icon = "link"
        label = "Link Section"
        group = GROUP_CALLOUTS
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


class _BaseImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False)


class ImageBlock(_BaseImageBlock):
    size = blocks.ChoiceBlock(
        choices=[
            ("small", "Small (400px)"),
            ("medium", "Medium (600px)"),
            ("large", "Large (800px)"),
        ],
        default="medium",
        required=True,
        help_text="Choose the size that best fits your content. Small for inline images, medium for standard content, large for featured images.",  # noqa: E501
    )

    class Meta:
        template = "components/streamfield/blocks/image_block.html"
        icon = "image"
        label = "Image"
        group = GROUP_MEDIA


class ImageGalleryBlock(blocks.StreamBlock):
    image = _BaseImageBlock(min_num=1)

    class Meta:
        template = "components/streamfield/blocks/image_gallery_block.html"
        icon = "image"
        label = "Image Gallery"
        group = GROUP_MEDIA


class TableBlock(BaseTableBlock):
    class Meta:
        template = "components/streamfield/blocks/table_block.html"
        icon = "table"
        label = "Table"
        help_text = "Create a table with rows and columns of data."
        group = GROUP_MEDIA


class MermaidDiagramBlock(blocks.StructBlock):
    diagram = blocks.TextBlock(required=True)
    title = blocks.CharBlock(required=False, help_text="Optional title/caption for the diagram")

    class Meta:
        template = "components/streamfield/blocks/mermaid_diagram_block.html"
        icon = "code"
        label = "Mermaid Diagram"
        help_text = "Create a Mermaid diagram."
        group = GROUP_MEDIA


class ProcessStepBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, help_text="The title of this step")
    description = blocks.RichTextBlock(required=True, help_text="A detailed description of this step")
    picture = ImageChooserBlock(required=False, help_text="An optional image to illustrate this step")

    class Meta:
        template = "components/streamfield/blocks/process_step_block.html"
        icon = "list-ol"
        label = "Process Step"
        help_text = "A single step in a process"
        group = GROUP_CALLOUTS


class ProcessScreenshotStepBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, help_text="The title of this step")
    description = blocks.RichTextBlock(required=False, help_text="A detailed description of this step")
    screenshot = ImageChooserBlock(required=True, help_text="A screenshot image for this step")

    class Meta:
        template = "components/streamfield/blocks/process_screenshot_step_block.html"
        icon = "image"
        label = "Process Step (Screenshot)"
        help_text = "A step that prominently displays a screenshot"
        group = GROUP_CALLOUTS


class ProcessStepStreamBlock(blocks.StreamBlock):
    step = ProcessStepBlock()
    screenshot_step = ProcessScreenshotStepBlock()


class ProcessSectionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, help_text="The heading for this section of steps")
    description = blocks.RichTextBlock(required=False, help_text="An optional description for this section")
    steps = ProcessStepStreamBlock(required=True, help_text="The steps in this section")

    class Meta:
        template = "components/streamfield/blocks/process_section_block.html"
        icon = "list-ul"
        label = "Process Section"
        help_text = "A section containing process steps"
        group = GROUP_CALLOUTS


class ProcessPageBlock(blocks.StreamBlock):
    section = ProcessSectionBlock()

    class Meta:
        icon = "list-ul"
        label = "Process Page"


class DosAndDontsItemBlock(blocks.StructBlock):
    item = blocks.CharBlock(required=True, help_text="The main item or heading")
    description = blocks.RichTextBlock(required=False, help_text="Optional detailed description or explanation")


class DosAndDontsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, help_text="Optional heading for the dos and don'ts section")
    dos_title = blocks.CharBlock(required=False, help_text="Custom title for the 'dos' section (defaults to 'Do')")
    donts_title = blocks.CharBlock(
        required=False, help_text="Custom title for the 'don'ts' section (defaults to 'Don't')"
    )
    dos = blocks.ListBlock(
        DosAndDontsItemBlock(),
        required=False,
        help_text="List of things to do",
    )
    donts = blocks.ListBlock(
        DosAndDontsItemBlock(),
        required=False,
        label="Don'ts",
        help_text="List of things not to do",
    )

    class Meta:
        template = "components/streamfield/blocks/dos_and_donts_block.html"
        icon = "list-ul"
        label = "Dos and Don'ts"
        help_text = "A list of recommended practices (dos) and things to avoid (don'ts)"
        group = GROUP_CALLOUTS


class StoryBlock(blocks.StreamBlock):
    accordion = AccordionBlock()
    mermaid_diagram = MermaidDiagramBlock()
    heading = HeadingBlock()
    text = RichTextBlock()
    quote = QuoteBlock()
    warning_callout = WarningCalloutBlock()
    dos_and_donts = DosAndDontsBlock()
    call_to_action = SnippetChooserBlock(
        "core.CallToAction",
        icon="megaphone",
        group=GROUP_CALLOUTS,
        template="components/streamfield/blocks/call_to_action_block.html",
    )
    links = LinkSectionBlock()
    image = ImageBlock()
    image_gallery = ImageGalleryBlock()
    table = TableBlock()
    document = DocumentChooserBlock(
        icon="doc-full-inverse",
        group=GROUP_MEDIA,
        template="components/streamfield/blocks/document_block.html",
    )


class HomePageBlock(blocks.StreamBlock):
    featured_sections = FeaturedSectionBlock()
    link_sections = LinkSectionBlock()
    call_to_action = SnippetChooserBlock(
        "core.CallToAction",
        icon="megaphone",
        group=GROUP_CALLOUTS,
        template="components/streamfield/blocks/call_to_action_block.html",
    )


class TopicPageBlock(HomePageBlock):
    heading = HeadingBlock()
    text = RichTextBlock()
    quote = QuoteBlock()
    warning_callout = WarningCalloutBlock()
