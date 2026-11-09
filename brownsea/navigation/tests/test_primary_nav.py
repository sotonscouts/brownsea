import pytest
from django.urls import reverse
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail_factories import ImageFactory

from brownsea.core.factories import CallToActionFactory
from brownsea.factories import InfoPageFactory
from brownsea.navigation.factories import NavigationSettingsFactory, nav_link
from brownsea.navigation.models import PrimaryNavigationLinkBlock


@pytest.fixture
def guides(site_tree):
    return InfoPageFactory(parent=site_tree["home"], title="Guides", slug="guides")


@pytest.fixture
def safeguarding(site_tree):
    return InfoPageFactory(parent=site_tree["home"], title="Safeguarding", slug="safeguarding")


def test_page_links_use_the_page_title_and_url(authenticated_client, site_tree, guides):
    NavigationSettingsFactory(site=site_tree["site"], primary_navigation=[nav_link(page=guides)])

    html = authenticated_client.get("/").content.decode()

    assert f'<a class="nav-link" href="{guides.url}">Guides</a>' in html


def test_link_title_overrides_the_page_title(authenticated_client, site_tree, guides):
    NavigationSettingsFactory(site=site_tree["site"], primary_navigation=[nav_link("Handy guides", page=guides)])

    html = authenticated_client.get("/").content.decode()

    assert ">Handy guides</a>" in html
    assert ">Guides</a>" not in html


def test_external_links_use_their_url(authenticated_client, site_tree):
    NavigationSettingsFactory(
        site=site_tree["site"], primary_navigation=[nav_link("Scouts", url="https://www.scouts.org.uk/")]
    )

    html = authenticated_client.get("/").content.decode()

    assert '<a class="nav-link" href="https://www.scouts.org.uk/">Scouts</a>' in html


def test_menus_list_their_groups_and_links(authenticated_client, site_tree, guides, safeguarding):
    NavigationSettingsFactory(
        site=site_tree["site"],
        primary_navigation=[nav_link("Resources", page=guides, groups={"Policies": [safeguarding]})],
    )

    html = authenticated_client.get("/").content.decode()

    assert 'data-bs-toggle="dropdown">Resources</a>' in html
    assert "Policies</h6>" in html
    assert f'href="{safeguarding.url}">Safeguarding</a>' in html
    # The heading of the menu links to the page the menu item points at.
    assert f'<a href="{guides.url}" class="link-primary text-decoration-none">Resources' in html


def test_menus_show_their_call_to_action(authenticated_client, site_tree, guides, safeguarding):
    call_to_action = CallToActionFactory(
        title="Volunteer today", link_text="Sign up", external_url="https://example.com/join"
    )
    NavigationSettingsFactory(
        site=site_tree["site"],
        primary_navigation=[
            nav_link("Resources", page=guides, groups={"Policies": [safeguarding]}, call_to_action=call_to_action)
        ],
    )

    html = authenticated_client.get("/").content.decode()

    assert "Volunteer today" in html
    assert 'href="https://example.com/join" class="btn btn-light">Sign up</a>' in html
    assert "card-img-top" not in html


def test_menus_show_their_featured_page_card(authenticated_client, site_tree, guides, safeguarding):
    featured = InfoPageFactory(
        parent=site_tree["home"], title="Camp guide", slug="camp-guide", introduction="Everything for camp"
    )
    NavigationSettingsFactory(
        site=site_tree["site"],
        primary_navigation=[
            nav_link(
                "Resources",
                page=guides,
                groups={"Policies": [safeguarding]},
                featured_page=featured,
                featured_image=ImageFactory(),
            )
        ],
    )

    html = authenticated_client.get("/").content.decode()

    assert f'<a href="{featured.url}" class="text-decoration-none">' in html
    assert "Camp guide</h4>" in html
    assert "Everything for camp" in html


def test_menus_without_a_featured_page_have_no_card(authenticated_client, site_tree, guides, safeguarding):
    NavigationSettingsFactory(
        site=site_tree["site"],
        primary_navigation=[nav_link("Resources", page=guides, groups={"Policies": [safeguarding]})],
    )

    html = authenticated_client.get("/").content.decode()

    assert "card-img-top" not in html


def test_the_logo_links_to_the_site_home(authenticated_client, site_tree):
    html = authenticated_client.get("/").content.decode()

    assert f'<a class="navbar-brand" href="{site_tree["home"].url}">' in html


def test_authenticated_users_get_search_and_logout(authenticated_client, site_tree):
    html = authenticated_client.get("/").content.decode()

    assert 'action="/search/"' in html
    assert f'action="{reverse("accounts:logout")}"' in html
    assert reverse("accounts:login") not in html


def test_anonymous_users_get_a_login_link_instead(client, site_tree):
    html = client.get(reverse("accounts:login")).content.decode()

    assert f'<a class="nav-link" href="{reverse("accounts:login")}">' in html
    assert f'action="{reverse("accounts:logout")}"' not in html
    assert 'action="/search/"' not in html


def test_the_menu_is_hidden_from_anonymous_users_by_default(client, site_tree, guides, settings):
    settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED = False
    NavigationSettingsFactory(site=site_tree["site"], primary_navigation=[nav_link(page=guides)])

    html = client.get(reverse("accounts:login")).content.decode()

    assert f'href="{guides.url}"' not in html


def test_the_menu_can_be_shown_to_anonymous_users(client, site_tree, guides, settings):
    settings.APP_SHOW_MENU_WHEN_UNAUTHENTICATED = True
    NavigationSettingsFactory(site=site_tree["site"], primary_navigation=[nav_link(page=guides)])

    html = client.get(reverse("accounts:login")).content.decode()

    assert f'<a class="nav-link" href="{guides.url}">Guides</a>' in html


def test_a_menu_cannot_have_both_a_call_to_action_and_a_featured_page(site_tree, guides, safeguarding):
    block = PrimaryNavigationLinkBlock()
    value = nav_link("Resources", page=guides, groups={"Policies": [safeguarding]})["value"]
    value["callout"] = [
        {"type": "call_to_action", "value": CallToActionFactory().pk},
        {"type": "featured_page", "value": {"page": safeguarding.pk, "image": ImageFactory().pk}},
    ]

    with pytest.raises(StructBlockValidationError) as error:
        block.clean(block.to_python(value))

    assert "callout" in error.value.block_errors
