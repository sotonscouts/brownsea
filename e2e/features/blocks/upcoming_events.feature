Feature: Upcoming events block
  The upcoming events block lists the next events, soonest first, and links to the full events index.

  Background:
    Given the intranet has a site
    And I am logged in
    And the site has an events index

  Scenario: The body shows the next four events as cards and links to every event
    Given the events are:
      | title    | starts     | type |
      | Event 1  | 2099-05-01 | Camp |
      | Event 2  | 2099-05-02 | Camp |
      | Event 3  | 2099-05-03 | Camp |
      | Event 4  | 2099-05-04 | Camp |
      | Event 5  | 2099-05-05 | Camp |
    And the home page body shows upcoming events as cards
    When I visit "/"
    Then I see the text "Event 1"
    And I see the text "Event 4"
    And I do not see the text "Event 5"
    When I click "View all events"
    Then I am on "/events/"

  Scenario: The sidebar shows a compact list
    Given the events are:
      | title       | starts     | type |
      | Spring Camp | 2099-05-01 | Camp |
    And the home page sidebar shows upcoming events
    When I visit "/"
    Then I see the text "Coming up"
    And I see the text "Spring Camp"

  Scenario: Nothing is shown when no events are coming up
    Given the events are:
      | title    | starts     | type |
      | Old Camp | 2020-04-30 | Camp |
    And the home page body shows upcoming events as cards
    When I visit "/"
    Then I do not see the text "Upcoming events"
