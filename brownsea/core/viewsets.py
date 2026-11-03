from wagtail.snippets.views.snippets import SnippetViewSet

from brownsea.core.models import Audience


class TaxonomyViewSet(SnippetViewSet):
    """Admin for a `Taxonomy` subclass. Add each one to the Taxonomies group in `core/wagtail_hooks.py`."""

    list_display = ("name", "slug")
    search_fields = ("name",)


class AudienceViewSet(TaxonomyViewSet):
    model = Audience
    menu_label = "Audiences"
