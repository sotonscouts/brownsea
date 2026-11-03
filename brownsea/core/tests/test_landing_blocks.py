import pytest
from wagtail.blocks import StreamBlockValidationError

from brownsea.core.blocks import HeadingBlock, LandingPageSidebarBlock, TaskTileValue
from brownsea.core.icons import DEFAULT_TASK_ICON, TASK_ICONS, task_icon_class


def test_heading_can_be_visually_hidden():
    block = HeadingBlock()

    hidden = block.render(block.to_python({"heading": "Sections", "visually_hidden": True}))
    shown = block.render(block.to_python({"heading": "Sections"}))

    assert "visually-hidden" in hidden
    assert "visually-hidden" not in shown


def test_unknown_task_icons_fall_back_to_the_default():
    assert task_icon_class("password") == TASK_ICONS["password"][1]
    assert task_icon_class("nope") == TASK_ICONS[DEFAULT_TASK_ICON][1]
    assert TaskTileValue(None, [("icon", "help")]).icon_class == TASK_ICONS["help"][1]


def test_sidebar_allows_one_quick_links_block():
    block = LandingPageSidebarBlock()
    link = {"type": "external_link", "value": {"url": "https://example.org", "title": "x"}}
    quick_links = {"type": "quick_links", "value": {"heading": "Quick links", "links": [link]}}

    block.clean(block.to_python([quick_links]))
    with pytest.raises(StreamBlockValidationError):
        block.clean(block.to_python([quick_links, quick_links]))


def test_quick_links_are_capped_at_six():
    block = LandingPageSidebarBlock()
    link = {"type": "external_link", "value": {"url": "https://example.org", "title": "x"}}
    seven = [{"type": "quick_links", "value": {"heading": "Quick links", "links": [link] * 7}}]

    with pytest.raises(StreamBlockValidationError):
        block.clean(block.to_python(seven))
