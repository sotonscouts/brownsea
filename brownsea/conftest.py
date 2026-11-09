import pytest
from wagtail.models import Page, Site

from brownsea.factories import HomePageFactory, publish


@pytest.fixture(autouse=True)
def _temporary_media(settings, tmp_path):
    """Keep uploaded test images out of the real media folder."""
    settings.MEDIA_ROOT = str(tmp_path / "media")


@pytest.fixture
def site_tree(db):
    site = Site.objects.get(is_default_site=True)
    site.hostname = "testserver"
    site.port = 80

    root = Page.get_first_root_node()
    home = publish(
        HomePageFactory(
            parent=root,
            title="Home",
            slug="test-home",
        )
    )
    site.root_page = home
    site.save()

    return {"root": root, "home": home, "site": site}


@pytest.fixture
def user(db):
    from brownsea.factories import UserFactory

    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def plain_static_files(settings):
    """Render pages (the Wagtail admin) that need static files without a `collectstatic` manifest."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
