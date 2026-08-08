import pytest
from wagtail.models import Page, Site

from brownsea.factories import HomePageFactory, publish


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

    return {"root": root, "home": home}


@pytest.fixture
def user(db):
    from brownsea.factories import UserFactory

    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
