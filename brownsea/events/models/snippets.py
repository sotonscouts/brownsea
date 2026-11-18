from brownsea.core.models import Taxonomy

__all__ = ["EventTopic", "EventType"]


class EventType(Taxonomy):
    """What kind of event it is, such as a camp or a meeting. One per event."""

    class Meta(Taxonomy.Meta):
        verbose_name = "Event Type"
        verbose_name_plural = "Event Types"


class EventTopic(Taxonomy):
    """What the event is about, such as programme or training. An event can have several."""

    class Meta(Taxonomy.Meta):
        verbose_name = "Event Topic"
        verbose_name_plural = "Event Topics"
