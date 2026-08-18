from wagtail.models import Site

from brownsea.core.themes import DEFAULT_THEME


def site_theme(request):
    from brownsea.core.models import ThemeSettings

    theme_settings = getattr(request, "preview_theme_settings", None)
    if theme_settings is None:
        site = Site.find_for_request(request)
        if site is not None:
            theme_settings = ThemeSettings.for_site(site)

    return {
        "theme_settings": theme_settings,
        "site_theme": theme_settings.theme if theme_settings is not None else DEFAULT_THEME,
    }
