Feature: Featured event block
  A featured event promotes one event on the home page. It stays after the event has ended, and disappears only if the event is unpublished.

  Background:
    Given the intranet has a site
    And I am logged in
    And the site has an events index

  Scenario: The home page promotes the chosen event and opens it
    Given the events are:
      | title         | starts     | type | location      | introduction            |
      | District Camp | 2099-04-30 | Camp | Foxlease Park | Three days under canvas |
    And the home page features the event "District Camp"
    When I visit "/"
    Then I see the text "Featured event"
    And I see the text "District Camp"
    And I see the text "Three days under canvas"
    When I click "View event"
    Then I am on "/events/district-camp/"

  Scenario: An event that has ended is still promoted
    Given the events are:
      | title    | starts     | type |
      | Old Camp | 2020-04-30 | Camp |
    And the home page features the event "Old Camp"
    When I visit "/"
    Then I see the text "Featured event"
    And I see the text "Old Camp"
