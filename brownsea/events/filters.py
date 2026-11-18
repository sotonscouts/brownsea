from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone

from brownsea.core.filters import AudienceFilter, FacetFilterSet, TaxonomyFilter
from brownsea.events.models.pages import EventPage
from brownsea.events.models.snippets import EventTopic, EventType


def _listed_events(under, *, finished):
    """Live events shown in listings that have finished or have not. An event runs to the end of its last day."""
    events = EventPage.objects.live().filter(show_in_menus=True)
    if under is not None:
        events = events.descendant_of(under)
    events = events.annotate(
        ends_on=Coalesce("end_date", "start_date", output_field=models.DateField())
    ).select_related("event_type")
    if finished:
        return events.filter(ends_on__lt=timezone.localdate()).order_by("-start_date", "-start_time", "title")
    return events.filter(ends_on__gte=timezone.localdate()).order_by("start_date", "start_time", "title")


def upcoming_events(under=None):
    """Events that have not finished, soonest first."""
    return _listed_events(under, finished=False)


def past_events(under=None):
    """Events that have finished, most recent first."""
    return _listed_events(under, finished=True)


class EventFilterSet(FacetFilterSet):
    type = TaxonomyFilter(EventType.objects.all(), field_name="event_type", label="Type")
    audience = AudienceFilter()
    topic = TaxonomyFilter(EventTopic.objects.all(), field_name="topics", label="Topic")
