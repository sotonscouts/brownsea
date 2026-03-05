from django.db import models
from wagtail.admin.panels import FieldPanel

__all__ = ["ExternalEventCalendar"]


class ExternalEventCalendar(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    ics_url = models.URLField()

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("ics_url"),
    ]

    class Meta:
        verbose_name = "External Event Calendar"
        verbose_name_plural = "External Event Calendars"
        ordering = ["name"]

    def __str__(self):
        return self.name
