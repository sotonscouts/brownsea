Feature: Event page
  An event shows when and where it happens, who it is for, what type it is and what it costs. A simple event shows
  those details across the page. An event with body content or sidebar blocks moves them into the sidebar. Which rows
  appear, and how dates and costs are written, is covered by unit tests; this checks what a visitor sees and can do.

  Background:
    Given the intranet has a site
    And I am logged in
    And the site has an events index

  Scenario: An event shows its title, introduction and details
    Given the events are:
      | title                  | starts     | type     | introduction                             |
      | Safeguarding Refresher | 2026-11-17 | Training | A short online session to stay in date |
    When I visit "/events/safeguarding-refresher/"
    Then I see the heading "Safeguarding Refresher"
    And I see the text "A short online session to stay in date"
    And the browser tab is titled "Safeguarding Refresher"
    And the breadcrumbs are "Home > Events"

  Scenario: The details show when, where, who it is for, the type and the cost
    Given the events are:
      | title                  | starts     | from  | to    | location | type     | audiences | cost |
      | Safeguarding Refresher | 2026-11-17 | 19:30 | 21:00 | Online   | Training | Volunteers | 0   |
    When I visit "/events/safeguarding-refresher/"
    Then the event details are:
      | When         | Tuesday 17 November 2026 19:30 to 21:00 |
      | Where        | Online                                  |
      | Who it's for | Volunteers                              |
      | Type         | Training                                |
      | Cost         | Free                                    |

  Scenario: Details with nothing to show are left out
    Given the events are:
      | title                  | starts     | type     |
      | Safeguarding Refresher | 2026-11-17 | Training |
    When I visit "/events/safeguarding-refresher/"
    Then the event details are:
      | When | Tuesday 17 November 2026 |
      | Type | Training                 |

  Scenario: A simple event shows its details across the page in columns
    Given the events are:
      | title                  | starts     | location | type     | audiences  | cost |
      | Safeguarding Refresher | 2026-11-17 | Online   | Training | Volunteers | 0    |
    When I visit "/events/safeguarding-refresher/"
    Then the event details span the full width of the page
    And the event details are laid out in columns
    And there is no sidebar

  Scenario: An event with body content puts its details beside the body
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the body:
      | block   | value             |
      | heading | Welcome           |
      | text    | Our biggest camp  |
    When I visit "/events/district-camp/"
    Then the event details sit beside the body, which takes about two thirds of the page
    And the event details are in one column

  Scenario: An event with only sidebar blocks also puts its details in the sidebar
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the key dates:
      | when             | what          |
      | 1st April 2027   | NAN forms due |
    When I visit "/events/district-camp/"
    Then the event details sit beside the body, which takes about two thirds of the page
    And the key dates are below the event details

  Scenario: On a phone the details come before the body
    Given I am using a phone
    And the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the body:
      | block | value            |
      | text  | Our biggest camp |
    And the event "District Camp" has the key dates:
      | when           | what          |
      | 1st April 2027 | NAN forms due |
    When I visit "/events/district-camp/"
    Then the event details are above the body
    And the key dates are below the body

  Scenario: The body shows its blocks in the order they were written
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the body:
      | block   | value             |
      | heading | Before you go     |
      | text    | Check the weather |
      | heading | When you arrive   |
      | text    | Find the campsite |
    When I visit "/events/district-camp/"
    Then the event body reads:
      | Before you go     |
      | Check the weather |
      | When you arrive   |
      | Find the campsite |

  Scenario: Key dates are listed under their heading
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the key dates:
      | when                       | what                               |
      | 1st December 2026          | Groups to submit predicted numbers |
      | 30th April to 3rd May 2027 | District Camp                      |
    When I visit "/events/district-camp/"
    Then the key dates read:
      | 1st December 2026          | Groups to submit predicted numbers |
      | 30th April to 3rd May 2027 | District Camp                      |

  Scenario: A key date can link to another event
    Given the events are:
      | title                   | starts     | type    |
      | District Camp           | 2027-04-30 | Camp    |
      | Camp Group Info Meeting | 2026-11-18 | Meeting |
    And the event "District Camp" has the key dates:
      | when             | what                    | links to                |
      | 18th November    | Group Info Meeting      | Camp Group Info Meeting |
      | 1st April 2027   | NAN forms due           |                         |
    When I visit "/events/district-camp/"
    And I click the key date "Group Info Meeting"
    Then I am on "/events/camp-group-info-meeting/"
    And I see the heading "Camp Group Info Meeting"

  Scenario: A key date without a link is plain text
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the key dates:
      | when           | what          |
      | 1st April 2027 | NAN forms due |
    When I visit "/events/district-camp/"
    Then the key date "NAN forms due" is not a link

  Scenario: Audience and type open the events index filtered to them
    Given the events are:
      | title                  | starts     | type     | audiences  |
      | Safeguarding Refresher | 2026-11-17 | Training | Volunteers |
    When I visit "/events/safeguarding-refresher/"
    And I click the event detail "Volunteers"
    Then I am on "/events/?audience=volunteers"
    When I visit "/events/safeguarding-refresher/"
    And I click the event detail "Training"
    Then I am on "/events/?type=training"

  Scenario: An event lists its sub-pages and opens one
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the child pages block
    And the page "District Camp" has the info pages:
      | title                | introduction              |
      | Code of conduct      | How we behave at camp     |
      | Arrivals             | When and where to arrive  |
    When I visit "/events/district-camp/"
    Then I see the cards:
      | Code of conduct |
      | Arrivals        |
    When I open the card "Code of conduct"
    Then I see the heading "Code of conduct"
    And the breadcrumbs are "Home > Events > District Camp"

  Scenario: The events index lists the events
    Given the events are:
      | title                  | starts     | type     |
      | Safeguarding Refresher | 2026-11-17 | Training |
      | District Camp          | 2027-04-30 | Camp     |
    When I visit "/events/"
    Then the events index lists:
      | Safeguarding Refresher |
      | District Camp          |

  Scenario: An event page loads without browser errors
    Given the events are:
      | title         | starts     | type |
      | District Camp | 2027-04-30 | Camp |
    And the event "District Camp" has the body:
      | block | value            |
      | text  | Our biggest camp |
    When I visit "/events/district-camp/"
    Then the browser reported no errors
