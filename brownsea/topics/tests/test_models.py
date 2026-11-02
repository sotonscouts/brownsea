import json

import pytest

from brownsea.factories import InfoPageFactory, publish
from brownsea.topics.models import TopicPage


@pytest.mark.django_db
def test_featured_page_ids_include_logo_grid_pages(site_tree):
    home = site_tree["home"]
    in_logos = publish(InfoPageFactory(parent=home, title="Logo", slug="logo"))
    in_links = publish(InfoPageFactory(parent=home, title="Link", slug="link"))
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

    ids = topic.get_featured_page_ids()

    assert in_logos.id in ids
    assert in_links.id in ids
    assert other.id not in ids
