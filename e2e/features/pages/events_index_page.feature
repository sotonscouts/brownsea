Feature: Events index page
  The events index lists upcoming events soonest first, grouped by month, with a tab for past events and filters for
  type, audience and topic. How events are ordered and filtered is covered by unit tests; this checks what a visitor
  sees and can do. Dates are far in the future, or well in the past, so the scenarios do not go stale.

  Background:
    Given the intranet has a site
    And I am logged in
    And the site has an events index

  Scenario: The events index lists upcoming events soonest first under month headings and opens them
    Given the events are:
      | title             | starts     | type     |
      | Leaders' social   | 2099-02-12 | Social   |
      | Winter camp       | 2099-01-23 | Camp     |
      | Safeguarding      | 2099-01-10 | Training |
      | Finished long ago | 2020-01-10 | Camp     |
    When I visit "/events/"
    Then I see the heading "Events"
    And the events index lists:
      | Safeguarding    |
      | Winter camp     |
      | Leaders' social |
    And the month headings read:
      | January 2099  |
      | February 2099 |
    When I open the events index item "Winter camp"
    Then I am on "/events/winter-camp/"
    And I see the heading "Winter camp"

  Scenario: A row shows its date, time, place, audiences and type
    Given the events are:
      | title        | starts     | from  | to    | location | type     | audiences                              |
      | Safeguarding | 2099-01-10 | 19:30 | 21:00 | Online   | Training | Volunteers, Cubs, Scouts, Beavers, Trustees |
    When I visit "/events/"
    Then the events index item "Safeguarding" shows the date tile "Jan 10"
    And the date tile of "Safeguarding" is to the left of its title and has a coloured month
    And the events index item "Safeguarding" shows "10 January 2099, 19:30 to 21:00"
    And the events index item "Safeguarding" shows "Online"
    And the events index item "Safeguarding" shows "Training"
    And the events index item "Safeguarding" shows "Beavers"
    And the events index item "Safeguarding" shows "+2"

  Scenario: The Past events tab lists finished events, most recent first, and Upcoming brings the rest back
    Given the events are:
      | title        | starts     | type     |
      | Old camp     | 2020-03-05 | Camp     |
      | Recent talk  | 2020-06-01 | Training |
      | Coming up    | 2099-01-10 | Camp     |
    When I visit "/events/"
    And I open the "Past events" tab
    Then I am on "/events/?tab=past"
    And the events index lists:
      | Recent talk |
      | Old camp    |
    When I open the "Upcoming" tab
    Then I am on "/events/"
    And the events index lists:
      | Coming up |

  Scenario: Ticking a filter narrows the list, and clearing it brings everything back
    Given the events are:
      | title        | starts     | type     | audiences  |
      | Winter camp  | 2099-01-23 | Camp     | Cubs       |
      | Safeguarding | 2099-01-10 | Training | Volunteers |
      | Summer camp  | 2099-07-04 | Camp     | Scouts     |
    When I visit "/events/"
    And I tick the filter "Camp"
    And I apply the filters
    Then I am on "/events/?type=camp"
    And the events index lists:
      | Winter camp |
      | Summer camp |
    And the filter "Camp" is ticked
    And the filter "Training" is not ticked
    When I tick the filter "Scouts"
    And I apply the filters
    Then the events index lists:
      | Summer camp |
    When I clear the filters
    Then I am on "/events/"
    And the events index lists:
      | Safeguarding |
      | Winter camp  |
      | Summer camp  |

  Scenario: A badge on a row opens the events index filtered to it
    Given the events are:
      | title        | starts     | type     | audiences  |
      | Winter camp  | 2099-01-23 | Camp     | Cubs       |
      | Safeguarding | 2099-01-10 | Training | Volunteers |
    When I visit "/events/"
    And I click the badge "Volunteers" on the events index item "Safeguarding"
    Then I am on "/events/?audience=volunteers"
    And the events index lists:
      | Safeguarding |

  Scenario: Filters stay when switching tab, and filtering keeps the tab
    Given the events are:
      | title       | starts     | type     |
      | Old camp    | 2020-03-05 | Camp     |
      | Old talk    | 2020-06-01 | Training |
      | Winter camp | 2099-01-23 | Camp     |
    When I visit "/events/?type=camp"
    And I open the "Past events" tab
    Then I am on "/events/?type=camp&tab=past"
    And the events index lists:
      | Old camp |
    When I tick the filter "Training"
    And I apply the filters
    Then the events index lists:
      | Old talk |
      | Old camp |

  Scenario: Long lists are split into pages that keep the filters
    Given events are shown 2 to a page
    And the events are:
      | title | starts     | type |
      | One   | 2099-01-01 | Camp |
      | Two   | 2099-01-02 | Camp |
      | Three | 2099-01-03 | Camp |
      | Four  | 2099-01-04 | Talk |
    When I visit "/events/"
    Then the events index lists:
      | One |
      | Two |
    When I click "2"
    Then I am on "/events/?page=2"
    And the events index lists:
      | Three |
      | Four  |
    When I visit "/events/?type=camp"
    And I click "Next"
    Then I am on "/events/?type=camp&page=2"
    And the events index lists:
      | Three |

  Scenario: On a phone the filters are tucked away until they are opened
    Given I am using a phone
    And the events are:
      | title       | starts     | type |
      | Winter camp | 2099-01-23 | Camp |
    When I visit "/events/"
    Then the filter "Camp" is hidden
    When I open the filters
    Then the filter "Camp" is shown
    When I tick the filter "Camp"
    And I apply the filters
    Then the filter "Camp" is shown and ticked
    And I see the filters button counting 1 active filter

  Scenario: An events index with no events says so
    When I visit "/events/"
    Then I see the text "There are no upcoming events."
    When I open the "Past events" tab
    Then I see the text "There are no past events."

  Scenario: Filters that match nothing say so
    Given the events are:
      | title        | starts     | type     | audiences  |
      | Winter camp  | 2099-01-23 | Camp     | Cubs       |
      | Safeguarding | 2099-01-10 | Training | Volunteers |
    When I visit "/events/"
    And I tick the filter "Camp"
    And I tick the filter "Volunteers"
    And I apply the filters
    Then I see the text "No events match these filters."
    When I clear the filters
    Then the events index lists:
      | Safeguarding |
      | Winter camp  |

  Scenario: The events index loads without browser errors
    Given the events are:
      | title       | starts     | type | location |
      | Winter camp | 2099-01-23 | Camp | Woodmill |
    When I visit "/events/"
    Then the browser reported no errors
