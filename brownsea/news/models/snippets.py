from django.db import models
from wagtail.admin.panels import FieldPanel


class NewsType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
    ]

    class Meta:
        verbose_name = "News Type"
        verbose_name_plural = "News Types"
        ordering = ["name"]

    def __str__(self):
        return self.name
