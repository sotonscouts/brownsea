Feature: Home page
  The home page welcomes people with an introduction and a search box, the sections the editors chose, and the latest
  news.

  Background:
    Given the intranet has a site
    And I am logged in

  Scenario: The home page shows its title and introduction
    Given the home page has the introduction "Everything for the unit, in one place"
    When I visit "/"
    Then the browser tab is titled "Home"
    And I see the text "Everything for the unit, in one place"
    And there are no breadcrumbs

  Scenario: The search form searches the site
    Given the site has an info page "Trip guide" with the body:
      | block | value             |
      | text  | Check the weather |
    When I visit "/"
    And I search for "weather" using the home page search form
    Then I am on "/search/?query=weather"
    And I see the search results:
      | Trip guide |

  Scenario: Featured items open their pages
    Given the site has an info page "Camp guide" with the introduction "Pitch a tent"
    And the site has an info page "Kit list" with the introduction "Pack a bag"
    And the home page has the sections:
      | section    | title      | page       | url |
      | featured 1 | Camp guide | Camp guide |     |
      | featured 1 | Kit list   | Kit list   |     |
    When I visit "/"
    Then I see the cards:
      | Camp guide |
      | Kit list   |
    And the card images have loaded
    When I open the card "Kit list"
    Then I am on "/kit-list/"
    And I see the heading "Kit list"

  Scenario: Link sections show a card for each page or site
    Given the site has an info page "Policies" with the introduction "Our rules"
    And the home page has the sections:
      | section | title  | page     | url                         |
      | links 1 | Policy | Policies |                             |
      | links 1 | Badges |          | https://badges.example.com/ |
    When I visit "/"
    Then I see the cards:
      | Policies |
      | Badges   |
    And I see the text "Our rules"
    And the card "Badges" links to "https://badges.example.com/"
    When I open the card "Policies"
    Then I am on "/policies/"

  Scenario: Sections appear in the order they were written
    Given the site has an info page "Camp guide"
    And the home page has the sections:
      | section    | title      | page       | url                         |
      | links 1    | First      |            | https://first.example.com/  |
      | featured 1 | Camp guide | Camp guide |                             |
      | links 2    | Last       |            | https://last.example.com/   |
    When I visit "/"
    Then I see the cards:
      | First      |
      | Camp guide |
      | Last       |

  Scenario: Recent news lists the latest three articles, newest first
    Given the site has a news index
    And the news has the articles:
      | title | published  | type         |
      | One   | 2026-01-01 | Announcement |
      | Two   | 2026-01-02 | Announcement |
      | Three | 2026-01-03 | Announcement |
      | Four  | 2026-01-04 | Announcement |
    When I visit "/"
    Then the recent news is:
      | Four  |
      | Three |
      | Two   |

  Scenario: Recent news shows each article's date and type
    Given the site has a news index
    And the news has the articles:
      | title | published  | type         |
      | Camp  | 2026-03-05 | Announcement |
    When I visit "/"
    Then the recent news item "Camp" shows the date "5 March 2026" and the type "Announcement"

  Scenario: Only the newest article is featured with its image and introduction
    Given the site has a news index
    And the news has the articles:
      | title | published  | type         | introduction      | image |
      | Older | 2026-03-01 | Announcement | Older intro       | yes   |
      | Lead  | 2026-03-05 | Announcement | Lead introduction | yes   |
    When I visit "/"
    Then the recent news item "Lead" shows its image and the introduction "Lead introduction"
    And the recent news item "Older" shows no image or introduction
    And the card images have loaded

  Scenario: Recent news links to the article and to all the news
    Given the site has a news index
    And the news has the articles:
      | title | published  | type         |
      | Camp  | 2026-03-05 | Announcement |
    When I visit "/"
    And I open the recent news item "Camp"
    Then I am on "/news/camp/"
    When I visit "/"
    And I click "View all news"
    Then I am on "/news/"
    And I see the heading "News"

  Scenario: There is no news card without a news index
    When I visit "/"
    Then there is no recent news

  Scenario: News filters set on the home page narrow the news and the link to all of it
    Given the site has a news index
    And the news has the articles:
      | title       | published  | type         | topics  |
      | Camp tips   | 2026-03-05 | Announcement | Camping |
      | Sailing day | 2026-03-04 | Announcement | Sailing |
      | Camp party  | 2026-03-03 | Event        | Camping |
    And the home page only shows news with the type "Announcement"
    And the home page only shows news with the topic "Camping"
    When I visit "/"
    Then the recent news is:
      | Camp tips |
    When I click "View all news"
    Then I am on "/news/?type=announcement&topic=camping"
    And the news index lists:
      | Camp tips |

  Scenario: The home page loads without browser errors
    Given the site has an info page "Camp guide"
    And the home page has the sections:
      | section    | title      | page       | url |
      | featured 1 | Camp guide | Camp guide |     |
    And the site has a news index
    And the news has the articles:
      | title | published  | type         | image |
      | Camp  | 2026-03-05 | Announcement | yes   |
    When I visit "/"
    Then the browser reported no errors
