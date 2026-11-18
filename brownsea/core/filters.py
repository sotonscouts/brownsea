import django_filters
from django import forms
from django.utils.functional import cached_property

from brownsea.core.models import Audience


class TaxonomyField(forms.ModelMultipleChoiceField):
    """Picks taxonomy values by slug. Slugs that no longer exist are ignored rather than failing the whole form."""

    def clean(self, value):
        known = set(self.queryset.values_list("slug", flat=True))
        return super().clean([slug for slug in value or [] if slug in known])


class TaxonomyFilter(django_filters.ModelMultipleChoiceFilter):
    """
    Narrows a listing by a taxonomy, chosen with checkboxes.

    An item matches if it has any of the chosen values. Choosing nothing means "any".
    """

    field_class = TaxonomyField

    def __init__(self, queryset, *, field_name, label, **kwargs):
        super().__init__(
            queryset=queryset,
            field_name=f"{field_name}__slug",
            to_field_name="slug",
            label=label,
            widget=forms.CheckboxSelectMultiple,
            **kwargs,
        )


class FacetFilterSet(django_filters.FilterSet):
    """
    The facets on a listing page. An item must match every facet that has values chosen.

    Declare each facet as a `TaxonomyFilter`. The listing template gets what it needs from `listing_context()`.
    """

    @cached_property
    def facets(self):
        """The facets worth showing, which are the ones that have any values to choose from."""
        return [field for field in self.form if field.field.queryset.exists()]

    @cached_property
    def active_count(self):
        return sum(len(self.form.cleaned_data.get(name) or []) for name in self.filters)

    def listing_context(self):
        return {
            "facet_filters": self.facets,
            "active_filter_count": self.active_count,
            "is_filtered": bool(self.active_count),
        }


class AudienceFilter(TaxonomyFilter):
    """The audiences a piece of content is for, which news and events both have."""

    def __init__(self, **kwargs):
        super().__init__(Audience.objects.all(), field_name="audiences", label="Audience", **kwargs)
