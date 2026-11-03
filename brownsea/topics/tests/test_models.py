import json

import pytest

from brownsea.factories import InfoPageFactory, publish
from brownsea.topics.models import TopicPage


@pytest.mark.django_db
def test_featured_page_ids_include_logo_grid_pages(site_tree):
    home = site_tree["home"]
    in_logos = publish(InfoPageFactory(parent=home, title="Logo", slug="logo"))
    in_links = publish(InfoPageFactory(parent=home, title="Link", slug="link"))
    in_quick = publish(InfoPageFactory(parent=home, title="Quick", slug="quick"))
    other = publish(InfoPageFactory(parent=home, title="Other", slug="other"))

    topic = TopicPage(title="Topic", slug="topic", introduction="Intro")
    topic.body = json.dumps(
        [
            {
                "type": "logo_grid",
                "id": "a",
                "value": [
                    {"type": "page", "id": "b", "value": {"page": in_logos.id, "image": None}},
                    {
                        "type": "external_link",
                        "id": "c",
                        "value": {"url": "https://example.org", "title": "Ext", "image": None},
                    },
                ],
            },
            {
                "type": "link_sections",
                "id": "d",
                "value": [{"type": "page", "id": "e", "value": {"page": in_links.id}}],
            },
        ]
    )

    topic.quick_links = json.dumps(
        [{"type": "page", "id": "f", "value": {"page": in_quick.id}}],
    )

    ids = topic.get_featured_page_ids()

    assert in_logos.id in ids
    assert in_links.id in ids
    assert in_quick.id in ids
    assert other.id not in ids


@pytest.mark.django_db
def test_new_topic_pages_cannot_be_created_but_existing_ones_stay_editable(admin_client, admin_user, site_tree):
    from django.urls import reverse

    home = site_tree["home"]
    topic = home.add_child(instance=TopicPage(title="Old topic", slug="old-topic", introduction="Intro", body=[]))

    add = admin_client.get(reverse("wagtailadmin_pages:add", args=["topics", "topicpage", home.pk]))

    assert TopicPage.can_create_at(home) is False
    assert add.status_code == 302
    assert add.url == reverse("wagtailadmin_home")
    assert topic.permissions_for_user(admin_user).can_edit()


def test_topic_pages_no_longer_have_news_fields():
    fields = TopicPage.get_edit_handler().get_form_class().base_fields

    assert "news_index_page" not in fields
    assert "news_content_type_plural" not in fields
