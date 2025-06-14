from collections import defaultdict

from django.forms.utils import ErrorList
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

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

    def clean(self, value):
        value = super().clean(value)
        errors = defaultdict(ErrorList)

        # Either a page or an external URL is required.
        if bool(value["page"]) == bool(value["external_url"]):
            errors["page"].append("Select either a page or enter an external URL.")

        # Make sure that title is required if using an external URL.
        if value["external_url"] and not value["title"]:
            errors["title"].append("A title is required if using an external URL.")

        if errors:
            raise StructBlockValidationError(errors)

        return value


class PrimaryNavigationLinkBlock(blocks.StructBlock):
    link = LinkBlock()
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

    class Meta:
        template = "components/navigation/includes/primary_nav_item.html"


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
