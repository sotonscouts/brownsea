import pytest
from django.test import RequestFactory
from wagtail.models import Site
from wagtail_factories import ImageFactory

from brownsea.core.models import ThemeSettings
from brownsea.core.themes import SCOUT_NAVY, SCOUT_PURPLE, THEMES, get_theme, hex_to_rgb


@pytest.mark.django_db
def test_default_theme_is_white(authenticated_client, site_tree):
    response = authenticated_client.get("/")

    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-theme="white"' in html
    assert f"--theme-primary: {SCOUT_PURPLE}" in html
    assert "--theme-navbar-bg: var(--bs-tertiary-bg)" in html


@pytest.mark.django_db
def test_purple_theme_updates_navbar_and_primary_colour(authenticated_client, site_tree):
    site = Site.objects.get(is_default_site=True)
    theme_settings = ThemeSettings.for_site(site)
    theme_settings.colour = "purple"
    theme_settings.save()

    response = authenticated_client.get("/")

    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-theme="purple"' in html
    assert f"--theme-primary: {SCOUT_PURPLE}" in html
    assert f"--theme-navbar-bg: {SCOUT_PURPLE}" in html
    assert "--theme-navbar-color: #ffffff" in html


@pytest.mark.django_db
def test_navy_theme_uses_white_text_on_brand_colour(authenticated_client, site_tree):
    site = Site.objects.get(is_default_site=True)
    theme_settings = ThemeSettings.for_site(site)
    theme_settings.colour = "navy"
    theme_settings.save()

    response = authenticated_client.get("/")

    html = response.content.decode()
    assert 'data-theme="navy"' in html
    assert f"--theme-primary: {SCOUT_NAVY}" in html
    assert f"--theme-navbar-bg: {SCOUT_NAVY}" in html
    assert "--theme-navbar-color: #ffffff" in html


@pytest.mark.django_db
def test_unit_name_is_shown_in_the_navbar(authenticated_client, site_tree):
    site = Site.objects.get(is_default_site=True)
    theme_settings = ThemeSettings.for_site(site)
    theme_settings.unit_name = "Test Unit"
    theme_settings.save()

    response = authenticated_client.get("/")

    assert b"Test Unit" in response.content


@pytest.mark.django_db
def test_default_logo_is_used_when_no_custom_logo_is_set(authenticated_client, site_tree):
    response = authenticated_client.get("/")

    html = response.content.decode()
    assert 'aria-label="Scouts logo"' in html
    assert 'class="logo-assembly__image"' in html


@pytest.mark.django_db
def test_custom_logo_replaces_the_default_logo(authenticated_client, site_tree):
    site = Site.objects.get(is_default_site=True)
    theme_settings = ThemeSettings.for_site(site)
    theme_settings.logo = ImageFactory(title="Custom unit logo")
    theme_settings.unit_name = "Hidden Unit"
    theme_settings.save()

    response = authenticated_client.get("/")

    html = response.content.decode()
    assert 'aria-label="Scouts logo"' not in html
    assert "logo-assembly__text" not in html
    assert "Hidden Unit" not in html
    assert "<img" in html
    assert "navbar-logo" in html


@pytest.mark.django_db
def test_theme_preview_uses_unsaved_colour(site_tree, user):
    site = Site.objects.get(is_default_site=True)
    theme_settings = ThemeSettings.for_site(site)
    theme_settings.colour = "blue"
    theme_settings.unit_name = "Preview Unit"

    request = RequestFactory().get("/", HTTP_HOST="testserver")
    request.user = user
    response = theme_settings.serve_preview(request, "")

    html = response.content.decode()
    assert 'data-theme="blue"' in html
    assert "--theme-navbar-bg: #006ddf" in html
    assert "Preview Unit" in html
    assert "Primary button" in html
    assert "navbar" in html


def test_available_themes():
    assert set(THEMES) == {"white", "purple", "navy", "blue", "red"}


def test_hex_to_rgb():
    assert hex_to_rgb("#490499") == "73, 4, 153"
    assert hex_to_rgb("00b8a3") == "0, 184, 163"


def test_unknown_theme_falls_back_to_white():
    theme = get_theme("teal")

    assert theme.slug == "white"
    assert theme.primary == SCOUT_PURPLE
