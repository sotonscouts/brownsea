from collections import defaultdict

from django.forms.utils import ErrorList
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.snippets.blocks import SnippetChooserBlock

from brownsea.core.models import CallToAction
from brownsea.core.utils import StreamField

from .struct_values import LinkStructValue


class LinkBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(required=False)
    external_url = blocks.URLBlock(required=False)
    title = blocks.CharBlock(
        help_text="Leave blank to use the page's own listing title or title. Required if using an external URL.",
        required=False,
    )

    class Meta:
        template = ("components/navigation/menu_item.html",)
        value_class = LinkStructValue

    def __init__(self, *args, link_required: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.link_required = link_required

    def clean(self, value):
        value = super().clean(value)
        errors = defaultdict(ErrorList)

        # Either a page or an external URL is required.
        if self.link_required and bool(value["page"]) == bool(value["external_url"]):
            errors["page"].append("Select either a page or enter an external URL.")

        # Make sure that title is required if using an external URL.
        if (not value["page"]) and (not value["title"]):
            errors["title"].append("A title is required unless linking to an internal page.")

        if errors:
            raise StructBlockValidationError(errors)

        return value


class PrimaryNavigationLinkBlock(blocks.StructBlock):
    link = LinkBlock(link_required=False)
    secondary_level_links = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("heading", blocks.CharBlock()),
                ("links", blocks.ListBlock(LinkBlock())),
            ]
        ),
        required=False,
        max_num=3,
        label="Columns",
        help_text=(
            "Add up to 3 columns of links for the mega menu. Leave blank if this link doesn't need a mega menu.",
        ),
    )
    call_to_action = SnippetChooserBlock(CallToAction, required=False)

    class Meta:
        template = "components/navigation/includes/primary_nav_item.html"

    def clean(self, value):
        value = super().clean(value)
        errors = defaultdict(ErrorList)
        if not value["link"].get_url() and not value["secondary_level_links"]:
            errors["link"].append("A link or secondary level links are required.")

        if errors:
            raise StructBlockValidationError(errors)
        return value


@register_setting(icon="list-ul")
class NavigationSettings(BaseSiteSetting, ClusterableModel):
    # Navigation
    primary_navigation = StreamField(
        [("link", PrimaryNavigationLinkBlock())],
        blank=True,
        help_text="Main site navigation",
    )

    panels = [
        FieldPanel("primary_navigation"),
    ]
