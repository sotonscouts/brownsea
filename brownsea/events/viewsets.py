from brownsea.core.viewsets import TaxonomyViewSet

from .models import EventTopic, EventType


class EventTypeViewSet(TaxonomyViewSet):
    model = EventType
    menu_label = "Event Types"


class EventTopicViewSet(TaxonomyViewSet):
    model = EventTopic
    menu_label = "Event Topics"
