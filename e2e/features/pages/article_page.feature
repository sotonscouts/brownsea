Feature: Article page
  An article is a news story with its date, type, author, topics and audiences, an introduction and a body.

  Background:
    Given the intranet has a site
    And I am logged in
    And the site has a news index

  Scenario: An article shows its title, introduction, date and type
    Given the news has the articles:
      | title     | published  | type         | introduction             |
      | Camp tips | 2026-03-05 | Announcement | Everything for the weekend |
    When I visit "/news/camp-tips/"
    Then I see the heading "Camp tips"
    And I see the text "Everything for the weekend"
    And the article is dated "5 March 2026" and typed "Announcement"
    And the browser tab is titled "Camp tips"
    And the breadcrumbs are "Home > News"

  Scenario: An article shows its image below the date and topics
    Given the news has the articles:
      | title     | published  | type         | introduction               | image |
      | Camp tips | 2026-03-05 | Announcement | Everything for the weekend | yes   |
    When I visit "/news/camp-tips/"
    Then the article image is below the date and above the introduction
    And the card images have loaded

  Scenario: A tall image is cropped so it does not push the article down the page
    Given the news has the articles:
      | title     | published  | type         | introduction               | image |
      | Camp tips | 2026-03-05 | Announcement | Everything for the weekend | tall  |
    When I visit "/news/camp-tips/"
    Then the article image is no taller than 40% of its width
    And the card images have loaded

  Scenario: An article shows its author
    Given the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    And the article "Camp tips" is written by "Sam Smith", the "County Commissioner"
    When I visit "/news/camp-tips/"
    Then I see the author "Sam Smith", the "County Commissioner"

  Scenario: An article without an author has no author card
    Given the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    When I visit "/news/camp-tips/"
    Then I do not see an author

  Scenario: The body shows its blocks in the order they were written
    Given the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    And the article "Camp tips" has the body:
      | block   | value             |
      | heading | Before you go     |
      | text    | Check the weather |
      | heading | When you arrive   |
      | text    | Find the campsite |
    When I visit "/news/camp-tips/"
    Then the article body reads:
      | Before you go     |
      | Check the weather |
      | When you arrive   |
      | Find the campsite |

  Scenario: Topic and audience badges open the news index filtered to them
    Given the news has the articles:
      | title       | published  | type         | topics  | audiences |
      | Camp tips   | 2026-03-05 | Announcement | Camping | Leaders   |
      | Sailing day | 2026-03-07 | Announcement | Sailing | Leaders   |
    When I visit "/news/camp-tips/"
    And I click the badge "Camping"
    Then I am on "/news/?topic=camping"
    And the news index lists:
      | Camp tips |
    When I visit "/news/camp-tips/"
    And I click the badge "Leaders"
    Then I am on "/news/?audience=leaders"
    And the news index lists:
      | Sailing day |
      | Camp tips   |

  Scenario: Articles with several headings get an in-page contents list
    Given the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    And the article "Camp tips" has the body:
      | block   | value             |
      | heading | Before you go     |
      | heading | When you arrive   |
      | heading | Before you leave  |
    When I visit "/news/camp-tips/"
    Then the contents list reads:
      | Before you go    |
      | When you arrive  |
      | Before you leave |

  Scenario: Articles can be found by searching for their content
    Given the news has the articles:
      | title     | published  | type         | introduction              |
      | Camp tips | 2026-03-05 | Announcement | Lanterns and marshmallows |
      | Boat day  | 2026-03-06 | Announcement | Life jackets              |
    When I visit "/"
    And I search for "marshmallows"
    Then I see the search results:
      | Camp tips |

  Scenario: An article loads without browser errors
    Given the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    When I visit "/news/camp-tips/"
    Then the browser reported no errors
