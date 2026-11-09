Feature: News index page
  The news index lists every published article, newest first, with filters for type, audience and topic.

  Background:
    Given the intranet has a site
    And I am logged in

  Scenario: The news index lists articles newest first and opens them
    Given the site has a news index
    And the news has the articles:
      | title       | published  | type         | introduction      |
      | Camp tips   | 2026-03-05 | Announcement | Pitch a tent      |
      | Sailing day | 2026-03-07 | Event        | Out on the water  |
    When I visit "/news/"
    Then I see the heading "News"
    And the news index lists:
      | Sailing day |
      | Camp tips   |
    And the news index item "Camp tips" shows the date "5 March 2026", the type "Announcement" and the text "Pitch a tent"
    When I open the news index item "Camp tips"
    Then I am on "/news/camp-tips/"
    And I see the heading "Camp tips"

  Scenario: Ticking a filter narrows the list, and clearing it brings everything back
    Given the site has a news index
    And the news has the articles:
      | title       | published  | type         | topics  |
      | Camp tips   | 2026-03-05 | Announcement | Camping |
      | Sailing day | 2026-03-07 | Announcement | Sailing |
      | Camp party  | 2026-03-03 | Event        | Camping |
    When I visit "/news/"
    And I tick the filter "Camping"
    And I apply the filters
    Then I am on "/news/?topic=camping"
    And the news index lists:
      | Camp tips  |
      | Camp party |
    And the filter "Camping" is ticked
    And the filter "Sailing" is not ticked
    When I clear the filters
    Then I am on "/news/"
    And the news index lists:
      | Sailing day |
      | Camp tips   |
      | Camp party  |

  Scenario: Filters combine, with values in one group as alternatives
    Given the site has a news index
    And the news has the articles:
      | title       | published  | type         | topics  | audiences |
      | Camp tips   | 2026-03-05 | Announcement | Camping | Leaders   |
      | Sailing day | 2026-03-07 | Announcement | Sailing | Leaders   |
      | Camp party  | 2026-03-03 | Event        | Camping | Leaders   |
      | Rover news  | 2026-03-01 | Announcement | Camping | Rovers    |
    When I visit "/news/"
    And I tick the filter "Camping"
    And I tick the filter "Sailing"
    And I tick the filter "Announcement"
    And I apply the filters
    Then the news index lists:
      | Sailing day |
      | Camp tips   |
      | Rover news  |
    When I tick the filter "Leaders"
    And I apply the filters
    Then the news index lists:
      | Sailing day |
      | Camp tips   |

  Scenario: Long lists are split into pages that keep the filters
    Given the site has a news index
    And news is shown 2 articles to a page
    And the news has the articles:
      | title | published  | type         | topics  |
      | One   | 2026-03-01 | Announcement | Camping |
      | Two   | 2026-03-02 | Announcement | Camping |
      | Three | 2026-03-03 | Announcement | Camping |
      | Four  | 2026-03-04 | Announcement | Sailing |
    When I visit "/news/"
    Then the news index lists:
      | Four  |
      | Three |
    When I click "2"
    Then I am on "/news/?page=2"
    And the news index lists:
      | Two |
      | One |
    When I visit "/news/?topic=camping"
    And I click "Next"
    Then I am on "/news/?topic=camping&page=2"
    And the news index lists:
      | One |

  Scenario: On a phone the filters are tucked away until they are opened
    Given I am using a phone
    And the site has a news index
    And the news has the articles:
      | title     | published  | type         | topics  |
      | Camp tips | 2026-03-05 | Announcement | Camping |
    When I visit "/news/"
    Then the filter "Camping" is hidden
    When I open the filters
    Then the filter "Camping" is shown
    When I tick the filter "Camping"
    And I apply the filters
    Then the filter "Camping" is shown and ticked
    And I see the filters button counting 1 active filter

  Scenario: A news index with no articles says so
    Given the site has a news index
    When I visit "/news/"
    Then I see the text "No articles have been published yet."

  Scenario: Filters that match nothing say so
    Given the site has a news index
    And the news has the articles:
      | title     | published  | type         | topics  |
      | Camp tips | 2026-03-05 | Announcement | Camping |
      | Boat day  | 2026-03-06 | Event        | Sailing |
    When I visit "/news/"
    And I tick the filter "Announcement"
    And I tick the filter "Sailing"
    And I apply the filters
    Then I see the text "No articles match these filters."
    When I clear the filters
    Then the news index lists:
      | Boat day  |
      | Camp tips |

  Scenario: A tall image does not stretch its card
    Given the site has a news index
    And the news has the articles:
      | title     | published  | type         | image |
      | Camp tips | 2026-03-05 | Announcement | tall  |
    When I visit "/news/"
    Then the news index item "Camp tips" is no taller than 300 pixels
    And the card images have loaded
    When I am using a phone
    And I visit "/news/"
    Then the news index item "Camp tips" is no taller than 500 pixels
    And the card images have loaded

  Scenario: The news index loads without browser errors
    Given the site has a news index
    And the news has the articles:
      | title     | published  | type         | image |
      | Camp tips | 2026-03-05 | Announcement | yes   |
    When I visit "/news/"
    Then the card images have loaded
    And the browser reported no errors
