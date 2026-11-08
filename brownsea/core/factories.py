import factory
from factory.django import DjangoModelFactory

from brownsea.core.models import AlertBannerSettings, CallToAction, ThemeSettings


class CallToActionFactory(DjangoModelFactory):
    class Meta:
        model = CallToAction

    title = factory.Sequence(lambda n: f"Call to action {n}")
    summary = "Find out more"
    link_text = "Find out more"
    external_url = "https://example.com/"


# Site settings are created lazily by Wagtail (`for_site`), so reuse the row if one already exists.
class ThemeSettingsFactory(DjangoModelFactory):
    class Meta:
        model = ThemeSettings
        django_get_or_create = ("site",)

    colour = "white"
    unit_name = "Test Unit"


class AlertBannerSettingsFactory(DjangoModelFactory):
    class Meta:
        model = AlertBannerSettings
        django_get_or_create = ("site",)

    enabled = True
    message = "Something you should know"
    type = "info"
