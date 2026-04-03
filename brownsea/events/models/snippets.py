from django.db import models
from wagtail.admin.panels import FieldPanel

__all__ = ["ExternalEventCalendar"]


class ExternalEventCalendar(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    ics_url = models.URLField()

    external_cors_origin = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional CORS origin to allow when fetching this calendar from an external website.",
    )
    external_bearer_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional Bearer token to include in the Authorization header when fetching this calendar.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("ics_url"),
        FieldPanel("external_cors_origin"),
        FieldPanel("external_bearer_token"),
    ]

    class Meta:
        verbose_name = "External Event Calendar"
        verbose_name_plural = "External Event Calendars"
        ordering = ["name"]

    def __str__(self):
        return self.name
