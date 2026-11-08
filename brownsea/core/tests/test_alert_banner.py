import pytest
from django.forms import ValidationError

from brownsea.core.factories import AlertBannerSettingsFactory
from brownsea.factories import InfoPageFactory


@pytest.fixture
def site(site_tree):
    return site_tree["site"]


def test_enabled_banner_shows_its_message_and_type(authenticated_client, site):
    AlertBannerSettingsFactory(site=site, message="Hut closed this weekend", type="warning")

    html = authenticated_client.get("/").content.decode()

    assert "Hut closed this weekend" in html
    assert "alert alert-warning" in html


def test_banner_is_not_shown_when_disabled(authenticated_client, site):
    AlertBannerSettingsFactory(site=site, enabled=False, message="Hut closed this weekend")

    html = authenticated_client.get("/").content.decode()

    assert "Hut closed this weekend" not in html


def test_banner_is_not_shown_without_a_message(authenticated_client, site):
    AlertBannerSettingsFactory(site=site, message="")

    html = authenticated_client.get("/").content.decode()

    assert 'role="alert"' not in html


def test_banner_is_not_shown_by_default(authenticated_client, site_tree):
    html = authenticated_client.get("/").content.decode()

    assert 'role="alert"' not in html


def test_banner_button_links_to_an_external_url(authenticated_client, site):
    AlertBannerSettingsFactory(site=site, button_text="Read more", button_external_url="https://example.com/news")

    html = authenticated_client.get("/").content.decode()

    assert 'href="https://example.com/news" class="btn btn-info btn-sm ms-3">' in html
    assert "Read more" in html


def test_banner_button_links_to_a_page(authenticated_client, site, site_tree):
    page = InfoPageFactory(parent=site_tree["home"], title="Hut closure", slug="hut-closure")
    AlertBannerSettingsFactory(site=site, button_text="Find out why", button_page=page)

    html = authenticated_client.get("/").content.decode()

    assert f'href="{page.url}" class="btn btn-info btn-sm ms-3">' in html


def test_banner_is_shown_on_the_login_page_to_anonymous_users(client, site):
    AlertBannerSettingsFactory(site=site, message="Hut closed this weekend")

    html = client.get("/accounts/login/").content.decode()

    assert "Hut closed this weekend" in html


@pytest.mark.django_db
def test_button_text_requires_a_link():
    banner = AlertBannerSettingsFactory.build(button_text="Read more")

    with pytest.raises(ValidationError, match="OR an external URL"):
        banner.clean()


@pytest.mark.django_db
def test_button_link_requires_text():
    banner = AlertBannerSettingsFactory.build(button_external_url="https://example.com/")

    with pytest.raises(ValidationError, match="Button text is required"):
        banner.clean()


def test_button_cannot_have_both_a_page_and_a_url(site, site_tree):
    page = InfoPageFactory(parent=site_tree["home"])
    banner = AlertBannerSettingsFactory.build(
        site=site, button_text="Read more", button_page=page, button_external_url="https://example.com/"
    )

    with pytest.raises(ValidationError, match="not both"):
        banner.clean()
