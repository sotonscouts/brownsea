from brownsea.core.models import Taxonomy

__all__ = ["NewsTopic", "NewsType"]


class NewsType(Taxonomy):
    """What kind of news it is, such as an announcement or a section update. One per article."""

    class Meta(Taxonomy.Meta):
        verbose_name = "News Type"
        verbose_name_plural = "News Types"


class NewsTopic(Taxonomy):
    """What the news is about, such as programme or governance. An article can have several."""

    class Meta(Taxonomy.Meta):
        verbose_name = "News Topic"
        verbose_name_plural = "News Topics"
