from pytest_bdd import scenarios, then

scenarios("blocks/featured_section.feature")

# Bootstrap's gutter eats a little of each column, so widths are compared as a share of the row with some slack.
FULL_WIDTH = 0.95
HALF_WIDTH = (0.4, 0.5)


def _boxes(page):
    row = page.locator("main .row.g-4").first.bounding_box()
    cards = [card.bounding_box() for card in page.locator("main .row.g-4 .card").all()]
    return row, cards


@then("the featured cards sit side by side, each half the width of the section")
def _side_by_side(page):
    row, cards = _boxes(page)
    assert len(cards) == 2
    first, second = cards
    assert first["y"] == second["y"]
    assert first["x"] + first["width"] <= second["x"]
    for card in cards:
        assert HALF_WIDTH[0] <= card["width"] / row["width"] <= HALF_WIDTH[1], (card, row)


@then("the featured card takes the full width of the section")
def _full_width(page):
    row, cards = _boxes(page)
    assert len(cards) == 1
    assert cards[0]["width"] / row["width"] >= FULL_WIDTH, (cards[0], row)
